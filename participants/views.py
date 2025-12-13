from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import UploadForm
from .models import Participant, Team
from .utils import assign_teams, build_email_content, build_report_workbook, parse_participants


@require_http_methods(["GET", "POST"])
def dashboard(request):
    upload_form = UploadForm()
    participants = list(Participant.objects.select_related("team").all())
    columns = []

    if request.method == "POST":
        if "file" in request.FILES:
            upload_form = UploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                Participant.objects.all().delete()
                team_map = {t.code: t for t in Team.objects.all()}
                parsed, columns = parse_participants(upload_form.cleaned_data["file"])
                team_names = {code: team.display_name for code, team in team_map.items() if team.display_name}
                teams_assigned = assign_teams(parsed, team_names)
                for team_info in teams_assigned:
                    team = team_map.get(team_info["name"]) or Team(code=team_info["name"])
                    team.display_name = team_info.get("display_name") or team.code
                    team.save()
                    team_map[team.code] = team
                    for member in team_info.get("members", []):
                        Participant.objects.create(
                            full_name=member.get("NOM ET PRENOM") or member.get("Nom") or "",
                            email=member.get("Email Address") or member.get("EMAIL") or "",
                            language_raw=member.get("language_raw", member.get("LANGUE", "")),
                            academic_level=member.get("academic_level", member.get("NIVEAU D'ETUDES", "")),
                            competences_raw=member.get("VOS COMPETENCES", ""),
                            skills_list=member.get("skills_list", []),
                            language_fr=member.get("language_fr", False),
                            language_en=member.get("language_en", False),
                            is_dev=member.get("is_dev", False),
                            is_marketing=member.get("is_marketing", False),
                            academic_score=member.get("academic_score", 0),
                            email_sent=member.get("email_sent", False),
                            is_leader=member.get("is_leader", False),
                            team=team,
                            uid=member.get("uid", ""),
                        )
                messages.success(request, "Fichier charge. Previsualisation ci-dessous.")
            else:
                messages.error(request, "Impossible de lire le fichier fourni.")
        else:
            action = request.POST.get("action")
            if action == "rename_team":
                team_name = request.POST.get("team_name")
                custom_name = (request.POST.get("custom_name") or "").strip()
                if not team_name:
                    messages.error(request, "Choisissez une equipe a renommer.")
                else:
                    team, _ = Team.objects.get_or_create(code=team_name)
                    team.display_name = custom_name or team.display_name or team.code
                    team.save()
                    messages.success(request, f"{team_name} devient '{team.display_name}'.")
            elif action == "add_mentor":
                team_name = request.POST.get("mentor_team")
                mentor_name = (request.POST.get("mentor_name") or "").strip()
                mentor_email = (request.POST.get("mentor_email") or "").strip()
                if not team_name:
                    messages.error(request, "Choisissez une equipe pour l'encadrant.")
                else:
                    team, _ = Team.objects.get_or_create(code=team_name)
                    team.mentor_name = mentor_name or "Encadrant"
                    team.mentor_email = mentor_email
                    team.save()
                    messages.success(request, f"Encadrant attribue a {team_name}.")
            elif action == "reset":
                Participant.objects.all().delete()
                Team.objects.all().delete()
                messages.info(request, "Base nettoyee. Chargez un nouveau fichier.")

    participants = list(Participant.objects.select_related("team").all())
    teams = build_teams_from_db()
    preview_rows = []
    for p in participants[:50]:
        preview_rows.append(
            {
                "NOM ET PRENOM": p.full_name,
                "Email Address": p.email,
                "LANGUE": p.language_raw,
                "NIVEAU D'ETUDES": p.academic_level,
                "VOS COMPETENCES": p.competences_raw,
            }
        )
    context = {
        "upload_form": upload_form,
        "columns": columns or ["NOM ET PRENOM", "Email Address", "LANGUE", "NIVEAU D'ETUDES", "VOS COMPETENCES"],
        "rows": preview_rows,
        "participants": participants,
        "teams": teams,
        "sender_choices": getattr(settings, "HACKATHON_ALLOWED_SENDERS", [settings.DEFAULT_FROM_EMAIL]),
    }
    return render(request, "participants/dashboard.html", context)


@require_POST
def send_emails_api(request):
    participants = list(Participant.objects.filter(email_sent=False))
    if not participants:
        return JsonResponse({"error": "Aucun participant a envoyer."}, status=400)

    sender_choices = getattr(settings, "HACKATHON_ALLOWED_SENDERS", [settings.DEFAULT_FROM_EMAIL])
    sender_email = request.POST.get("sender_email") or settings.DEFAULT_FROM_EMAIL
    if sender_email not in sender_choices:
        sender_email = settings.DEFAULT_FROM_EMAIL

    results = []
    to_send = participants

    for person in to_send:
        email = person.email
        full_name = person.full_name or "Participant"
        if not email:
            results.append({"status": "skipped", "email": None, "name": full_name, "message": "Pas d'email fourni."})
            continue

        subject, body = build_email_content(person.language_raw, full_name)
        try:
            send_mail(subject, body, sender_email, [email], fail_silently=False)
            person.email_sent = True
            person.save(update_fields=["email_sent"])
            results.append({"status": "sent", "email": email, "name": full_name, "message": "Envoye"})
        except Exception as exc:
            results.append({"status": "error", "email": email, "name": full_name, "message": str(exc)})

    success = len([r for r in results if r["status"] == "sent"])
    errors = len([r for r in results if r["status"] == "error"])

    return JsonResponse(
        {
            "results": results,
            "success": success,
            "errors": errors,
            "total": len(to_send),
        }
    )


@require_GET
def export_excel(request):
    participants = list(Participant.objects.select_related("team").all())
    if not participants:
        return HttpResponse("Aucun participant.", status=400)

    teams = build_teams_from_db()
    participants_data = [
        {
            "NOM ET PRENOM": p.full_name,
            "Email Address": p.email,
            "LANGUE": p.language_raw,
            "NIVEAU D'ETUDES": p.academic_level,
            "VOS COMPETENCES": p.competences_raw,
            "skills_list": p.skills_list,
            "language_raw": p.language_raw,
            "academic_level": p.academic_level,
            "email_sent": p.email_sent,
            "team": p.team.code if p.team else None,
            "team_display": p.team.display_name if p.team else None,
            "is_leader": p.is_leader,
        }
        for p in participants
    ]
    report_bytes = build_report_workbook(participants_data, teams, None)
    response = HttpResponse(
        report_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=hackathon_teams.xlsx"
    return response


def _apply_team_names(participants, team_names):
    for person in participants:
        team_key = person.get("team")
        if not team_key:
            continue
        person["team_display"] = team_names.get(team_key) or team_key
    return participants


def build_teams_from_db():
    teams = []
    team_map = {t.code: t for t in Team.objects.all()}
    participants = list(Participant.objects.select_related("team").all())
    for idx in range(10):
        name = f"TEAM {idx + 1}"
        team_obj = team_map.get(name) or Team(code=name, display_name=name)
        if not team_obj.pk:
            team_obj.save()
        members = [p for p in participants if p.team and p.team.code == name]
        leader = None
        if members:
            leader = max(members, key=lambda m: m.academic_score)
            for m in members:
                m.is_leader = m is leader
                m.save(update_fields=["is_leader"])
        teams.append(
            {
                "name": name,
                "display_name": team_obj.display_name or name,
                "members": [
                    {
                        "NOM ET PRENOM": m.full_name,
                        "Email Address": m.email,
                        "language_raw": m.language_raw,
                        "academic_level": m.academic_level,
                        "VOS COMPETENCES": m.competences_raw,
                        "skills_list": m.skills_list,
                        "team_display": team_obj.display_name or name,
                        "is_leader": m.is_leader,
                    }
                    for m in members
                ],
                "leader": leader,
                "mentor": {"name": team_obj.mentor_name, "email": team_obj.mentor_email}
                if (team_obj.mentor_name or team_obj.mentor_email)
                else None,
            }
        )
    return teams
