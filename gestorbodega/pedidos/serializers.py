from rest_framework import serializers
from .models import Entregador, Registros_Pedidos, Pedido

class Entregadores_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Entregador
        fields = "__all__"
        
class Registros_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Registros_Pedidos
        fields = "__all__"
                       
class PedidoSerializer(serializers.ModelSerializer):
    doc_entregador = Entregadores_Serializer(read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'documento', 'nombre_entregador', 'numero_ruta',
            'valor_pedido', 'numero_factura', 'tipo_pedido', 'acompanado',
            'acompanante', 'fecha', 'valor_transferencia', 'completado', 'usuario'
        ]
