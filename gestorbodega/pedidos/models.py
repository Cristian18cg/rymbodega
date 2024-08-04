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
        
  