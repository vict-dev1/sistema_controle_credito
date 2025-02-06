from rest_framework import serializers
from .models import Empresa, PER, Dcomp, DcompDebitos, PerCanc


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class PERSerializer(serializers.ModelSerializer):
    class Meta:
        model = PER
        fields = '__all__'

class DcompSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dcomp
        fields = '__all__'

class DcompDebitosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DcompDebitos
        fields = '__all__'

class PerCancSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerCanc
        fields = '__all__'