from django import forms
from perdcomp.models import Empresa

class PDFUploadForm(forms.Form):
    upload = forms.FileField(
        label="Selecione o PDF",
        help_text="Você pode enviar mais de um arquivo PDF.",
    )


class EmpresaForm(forms.Form):
    empresa = forms.ModelChoiceField(queryset=Empresa.objects.all(), empty_label="Selecione uma empresa")