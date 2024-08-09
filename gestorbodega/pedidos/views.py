from django.shortcuts import render
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import Entregadores_Serializer

from .models import Entregador, Registros_Pedidos
import os

# Create your views here.
class PedidosViews(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


    @action (detail=False, methods=['POST'])
    def crear_entregador(self, request): 
        if request.method == 'POST':
            try:
                nombres = request.POST.get('nombres')
                apellidos = request.POST.get('apellidos')
                vehiculo = request.POST.get('Vehiculo')
                documento = request.POST.get('documento')
                usuario = request.POST.get('usuario')
                try:
                    Entregador.objects.create(
                            documento=documento,
                            nombres=nombres,
                            apellidos=apellidos,
                            vehiculo=vehiculo) 
                    
                    entregador = Entregador.objects.filter(documento=documento).first()
                    if entregador :
                        Registros_Pedidos.objects.create(
                                    documento=entregador,
                                    nombre_responsable=usuario,
                                    tipo_registro='Nuevo',
                                    descripcion_registro=f'Se crea colaborador {nombres} {apellidos}')
                        return JsonResponse({'message': f'El colaborador fue creado correctamente: {nombres} {apellidos}. '}) 

                       
                except Exception as e: 
                    print(str(e))
                    return Response({'error': 'Ha ocurrido un error creando el colaborador en base de datos'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e: 
                print(str(e))
                
        else:
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    @action(detail=False, methods=['GET']) # obtener los registos necesarios de las notificaciones
    def lista_entregadores(self, request):
        try:
            queryset = Entregador.objects.all()
            serializer = Entregadores_Serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
             print("Error obteniendo el log", str(e))
             return Response({'error': f'Se produjo un error al obtener los registros de contrato activo {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        