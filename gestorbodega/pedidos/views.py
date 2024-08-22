from django.shortcuts import render
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, date
from django.db import transaction
from django.db.models import Count, Q
from .serializers import Entregadores_Serializer, PedidoSerializer
import json

from .models import Entregador, Registros_Pedidos, Pedido
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
                  
            # Verificar si el entregador ya existe
                if Entregador.objects.filter(documento=documento).exists():
                     return Response({'error': f'El colaborador con documento {documento} ya está creado en la base de datos.'}, status=status.HTTP_400_BAD_REQUEST)
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
    
    @action(detail=False, methods=['POST'])
    def crear_pedido(self, request):
        if request.method == 'POST':
            try:
                # Obtener datos del POST
                nombres = request.POST.get('nombres')
                documento = request.POST.get('documento')
                vehiculo = request.POST.get('Vehiculo')
                usuario = request.POST.get('usuario')
                acompañante = request.POST.get('Acompañante')
                acompañado = request.POST.get('Acompañado')

                # Intentar obtener y verificar los datos de pedidos
                pedidos_json = request.POST.get('pedidos')
                if not pedidos_json:
                    return Response({'error': 'No se recibió información de pedidos'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    pedidos_data = json.loads(pedidos_json)
                except json.JSONDecodeError:
                    return Response({'error': 'Formato de JSON de pedidos no válido'}, status=status.HTTP_400_BAD_REQUEST)

                if not isinstance(pedidos_data, list):
                    return Response({'error': 'La estructura de los pedidos debe ser una lista'}, status=status.HTTP_400_BAD_REQUEST)

                created_pedidos = []
                fecha_actual = datetime.now()
                   # Verificar si ya existe un pedido con el mismo número de ruta y entregador para la fecha actual
                for pedido in pedidos_data:
                 numero_ruta = pedido.get('numeroRuta', '')
                 
                 if Pedido.objects.filter(
                    documento__documento=documento,
                    numero_ruta=numero_ruta,
                    fecha__date=fecha_actual
                ).exists():
                    return Response({'error': 'El número de ruta ya está asignado para hoy para este entregador'}, status=status.HTTP_400_BAD_REQUEST)
                # Crear los pedidos uno a uno
                for pedido in pedidos_data:
                    if not isinstance(pedido, dict):
                        return Response({'error': 'Formato de pedido no válido'}, status=status.HTTP_400_BAD_REQUEST)

                    try:
                        entregador = Entregador.objects.filter(documento=documento).first()
                        if entregador :
                            pedido_obj = Pedido.objects.create(
                                documento=entregador,
                                nombre_entregador=nombres,
                                numero_ruta=pedido.get('numeroRuta', ''),
                                valor_pedido=pedido.get('valorPedido', 0),
                                numero_factura=pedido.get('numeroFactura', ''),
                                tipo_pedido=pedido.get('tipoPedido', ''),
                                tipo_vehiculo=vehiculo,
                                acompanado=acompañado == 'true',
                                acompanante=acompañante,
                                fecha=fecha_actual,
                                valor_transferencia =0,
                                devolucion =0,

                                creador=usuario
                            )
                            created_pedidos.append(pedido_obj)
                    except Exception as e:
                        print(str(e))
                        # En caso de error al crear un pedido, eliminar los pedidos ya creados
                        for pedido_obj in created_pedidos:
                            pedido_obj.delete()
                        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({'message': 'Pedidos creados correctamente'}, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse({'error': 'Método no permitido'}, status=405)

   
    @action(detail=True, methods=['DELETE'])
    def eliminar_pedido(self, request, pk=None):
        try:
            # Buscar el pedido por ID (pk)
            pedido = Pedido.objects.get(pk=pk)

            # Eliminar el pedido
            pedido.delete()

            return Response({'message': 'Pedido eliminado correctamente'}, status=status.HTTP_204_NO_CONTENT)
        except Pedido.DoesNotExist:
            return Response({'error': 'Pedido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ha ocurrido un error eliminando el pedido: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['GET'])
    def lista_entregadores(self, request):
        try:
            # Obtiene la fecha de hoy
            hoy = datetime.now().date()

            # Filtra los pedidos por la fecha de hoy y agrupa por entregador
            entregadores_con_pedidos = Pedido.objects.filter(fecha__date=hoy).values('documento').annotate(
                completados=Count('id', filter=Q(completado=True)),
                no_completados=Count('id', filter=Q(completado=False)),
                total_rutas=Count('id', filter=Q(completado=False), distinct=True)  # Cuenta las rutas únicas por entregador
            
            )

            # Obtiene los entregadores y añade las estadísticas de pedidos
            entregadores = Entregador.objects.filter(documento__in=[e['documento'] for e in entregadores_con_pedidos])
            data = []

            for entregador in entregadores:
                stats = next((e for e in entregadores_con_pedidos if e['documento'] == entregador.documento), None)
                
                data.append({
                    'documento':entregador.documento,
                    'entregador': f"{entregador.nombres} {entregador.apellidos}",
                    'completados': stats['completados'],
                    'no_completados': stats['no_completados'],
                    'total_rutas': stats['total_rutas'],  # Añadir el total de rutas

                })

            return Response(data)
        except Exception as e:
            print("Error obteniendo el log", str(e))
            return Response({'error': f'Se produjo un error al obtener los registros de entregadores {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=False, methods=['GET'])
    def lista_entregadores_total(self, request):
        try:
            queryset = Entregador.objects.all()
            serializer = Entregadores_Serializer(queryset, many=True)
            
            return Response(serializer.data)
        except Exception as e:
             print("Error obteniendo el log", str(e))
             return Response({'error': f'Se produjo un error al obtener los registros de contrato activo {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['GET'])
    def pedidos_por_entregador(self, request):
        try:
            # Obtener el documento del entregador desde los parámetros de la solicitud
            documento = request.query_params.get('documento', None)
            if not documento:
                return Response({'error': 'El parámetro "documento" es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
            # Verificar si el entregador existe
            entregador = Entregador.objects.filter(documento=documento).first()
            if not entregador:
                return Response({'error': 'Entregador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
            # Obtiene la fecha de hoy
            hoy = datetime.now().date()
    
            # Filtra los pedidos del día de hoy para el entregador y los agrupa por número de ruta
            pedidos = Pedido.objects.filter(documento=entregador, fecha__date=hoy).order_by('numero_ruta')
            rutas_agrupadas = {}
    
            for pedido in pedidos:
                ruta = pedido.numero_ruta
                if ruta not in rutas_agrupadas:
                    rutas_agrupadas[ruta] = []
                rutas_agrupadas[ruta].append({
                    'id': pedido.id,
                    'nombre_entregador': pedido.nombre_entregador,
                    'numero_ruta': ruta,
                    'valor_pedido': pedido.valor_pedido,
                    'numero_factura': pedido.numero_factura,
                    'tipo_pedido': pedido.tipo_pedido,
                    'tipo_vehiculo': pedido.tipo_vehiculo,
                    'acompanado': pedido.acompanado,
                    'acompanante': pedido.acompanante,
                    'fecha': pedido.fecha,
                    'valor_transferencia': pedido.valor_transferencia,
                    'devolucion': pedido.devolucion,
                    'completado': pedido.completado,
                    'creador': pedido.creador
                })
    
            # Construir la respuesta agrupada por número de ruta
            data = []
            for ruta, pedidos_lista in rutas_agrupadas.items():
                data.append({
                    'numero_ruta': ruta,
                    'pedidos': pedidos_lista
                })
    
            return Response(data)
        except Exception as e:
            print("Error obteniendo los pedidos", str(e))
            return Response({'error': f'Se produjo un error al obtener los pedidos: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
    @action(detail=False, methods=['PUT'])
    def actualizar_pedido(self, request):
        try:
            print("entreo")
            # Extraer los datos del request
            id_pedido = request.data.get('id')
            campo = request.data.get('campo')
            nuevo_dato = request.data.get('dato')
            usuario = request.data.get('usuario')
            documento = request.data.get('documento')

            # Validar que se hayan proporcionado todos los datos necesarios
            if not id_pedido or not campo or not nuevo_dato:
                return Response({'error': 'ID del pedido, campo y dato son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

            # Obtener el pedido a actualizar
            pedido = Pedido.objects.filter(id=id_pedido).first()
            if not pedido:
                return Response({'error': 'Pedido no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            # Obtener el dato antiguo antes de actualizar
            dato_viejo = getattr(pedido, campo)

            # Actualizar el campo dinámicamente
            setattr(pedido, campo, nuevo_dato)
            pedido.save()

            # Crear el registro solo si la actualización fue exitosa
            entregador = Entregador.objects.filter(documento=documento).first()
            if entregador:
                Registros_Pedidos.objects.create(
                    documento=entregador,
                    nombre_responsable=usuario,
                    tipo_registro='Actualizacion',
                    descripcion_registro=f'Se actualizó {campo}: dato viejo "{dato_viejo}", nuevo dato "{nuevo_dato}"'
                )

            return Response({'success': f'{campo} actualizado correctamente.'}, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error actualizando el pedido", str(e))
            return Response({'error': f'Se produjo un error al actualizar el pedido: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)