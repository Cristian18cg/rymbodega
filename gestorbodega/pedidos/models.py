from django.db import models

# Create your models here.
class Entregador(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    vehiculo = models.CharField(max_length=100)
    documento = models.CharField(primary_key=True, max_length=50, unique=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    class Meta:
        managed = True
        db_table = 'entregador'
 
class Registros_Pedidos(models.Model):
   
    id = models.BigAutoField(primary_key=True)
    documento = models.ForeignKey(Entregador, on_delete=models.CASCADE, db_column='documento', blank=True, null=True)
    nombre_responsable = models.CharField(max_length=100, blank=False, null=True)
    tipo_registro =  models.CharField(max_length=50, blank=True, null=True)
    hora_registro = models.DateTimeField(auto_now_add=True)
    descripcion_registro=models.CharField(max_length=250, blank=False, null=True)
    
    class Meta:
        managed = True
        db_table = 'registros_pedidos'
        

class Pedido(models.Model):
    id = models.AutoField(primary_key=True)
    documento = models.ForeignKey(Entregador, on_delete=models.CASCADE,  db_column='documento')
    nombre_entregador = models.CharField(max_length=100)
    numero_ruta = models.CharField(max_length=50)
    valor_pedido = models.DecimalField(max_digits=15, decimal_places=2)
    numero_factura = models.CharField(max_length=50)
    tipo_pedido = models.CharField(max_length=50)
    tipo_vehiculo = models.CharField(max_length=50)
    acompanado = models.BooleanField()
    acompanante = models.CharField(max_length=100, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    valor_transferencia = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    devolucion = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    completado = models.BooleanField(default=False)
    creador = models.CharField(max_length=50)

    def __str__(self):
        return f"Pedido {self.id} - {self.numero_factura}"

    class Meta:
        managed = False
        db_table = 'pedido'