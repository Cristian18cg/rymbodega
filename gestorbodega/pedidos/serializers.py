from rest_framework import serializers
from .models import Entregador, Registros_Pedidos

class Entregadores_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Entregador
        fields = "__all__"
        
class Registros_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Registros_Pedidos
        fields = "__all__"
                       