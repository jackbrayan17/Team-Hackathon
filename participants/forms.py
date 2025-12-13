from django import forms


class UploadForm(forms.Form):
    file = forms.FileField(
        label="Fichier Excel (.xlsx)",
        help_text="La premiere feuille doit contenir les colonnes 'Email Address', 'NOM ET PRENOM', 'LANGUE', \"NIVEAU D'ETUDES\", 'VOS COMPETENCES'.",
        widget=forms.ClearableFileInput(attrs={"class": "file-input"}),
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith((".xlsx", ".xls")):
            raise forms.ValidationError("Merci de fournir un fichier Excel (.xlsx ou .xls).")
        return uploaded
