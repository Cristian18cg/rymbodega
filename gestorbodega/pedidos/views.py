from django.shortcuts import render
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, date
from django.db import transaction, models
from django.db.models import Count, Q,Sum
from django.db.models.functions import TruncDate
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
                agregar = request.POST.get('agregar')
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
                if agregar == 'false'  :
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
                                efectivo=0,
                                base=pedido.get('base', 0),
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

    @action(detail=False, methods=['DELETE'])
    def eliminar_pedido(self, request):
        id_pedido = request.data.get('id')
        usuario = request.data.get('usuario')
        documento = request.data.get('documento')
    
        if not id_pedido or not usuario or not documento:
            return Response({'error': 'ID del pedido, usuario y documento son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            # Buscar el pedido por ID
            pedido = Pedido.objects.filter(id=id_pedido).first()
    
            if not pedido:
                return Response({'error': 'Pedido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
            # Eliminar el pedido
            pedido.delete()
    
            # Registrar la eliminación solo si el pedido fue eliminado
            entregador = Entregador.objects.filter(documento=documento).first()
            if entregador:
                Registros_Pedidos.objects.create(
                    documento=entregador,
                    nombre_responsable=usuario,
                    tipo_registro='Eliminacion',
                    descripcion_registro=f'Pedido con ID {id_pedido} eliminado.'
                )
    
            return Response({'message': 'Pedido eliminado correctamente'}, status=200)
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
                creditos=Count('id', filter=Q(credito=True)),
                total_rutas=Count('id', distinct=True),  # Cuenta las rutas únicas por entregador
                total_valor_pedido=Sum('valor_pedido'),
                total_valor_creditos=Sum('valor_pedido', filter=Q(credito=True) & Q(completado=False)),  # Suma del valor de los pedidos con crédito
                total_valor_no_completados=Sum('valor_pedido', filter=Q(credito=False) & Q(completado=False))  # Suma del valor de los pedidos no completados
            )

            # Obtiene los entregadores y añade las estadísticas de pedidos
            entregadores = Entregador.objects.filter(documento__in=[e['documento'] for e in entregadores_con_pedidos])
            data = []

            for entregador in entregadores:
                stats = next((e for e in entregadores_con_pedidos if e['documento'] == entregador.documento), None)
                
                data.append({
                    'documento': entregador.documento,
                    'entregador': f"{entregador.nombres} {entregador.apellidos}",
                    'completados': stats['completados'],
                    'no_completados': stats['no_completados'],
                    'total_rutas': stats['total_rutas'],  # Añadir el total de rutas
                    'total_valor': stats['total_valor_pedido'],  # Añadir el total de valor de pedidos
                    'total_valor_creditos': stats['total_valor_creditos'],  # Añadir el total de valor de créditos
                    'total_valor_no_completados': stats['total_valor_no_completados'],  # Añadir el total del valor de no completados
                    'total_valor_creditos': stats['total_valor_creditos'],  # Añadir el total del valor de no completados
                    'creditos': stats['creditos'],
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
                    'creador': pedido.creador,
                    'efectivo':pedido.efectivo,
                    'credito': pedido.credito,
                    'base': pedido.base,
                })
    
            # Construir la respuesta agrupada por número de ruta
            data = []
            for ruta, pedidos_lista in rutas_agrupadas.items():
                data.append({
                    'numero_ruta': ruta,
                    'pedidos': pedidos_lista,
                })
    
            return Response(data)
        except Exception as e:
            print("Error obteniendo los pedidos", str(e))
            return Response({'error': f'Se produjo un error al obtener los pedidos: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
    @action(detail=False, methods=['GET'])
    def obtener_ruta(self, request):
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
            
            # Obtener el último pedido del día de hoy para el entregador, ordenado por número de ruta en orden descendente
            ultimo_pedido = Pedido.objects.filter(documento=entregador.documento, fecha__date=hoy).order_by('-id').first()
            # Si no hay pedidos para el día de hoy, devolver 1
            if not ultimo_pedido:
                return Response({'numero_ruta': 0}, status=status.HTTP_200_OK)
            ultima_base = ultimo_pedido.base         
            # Extraer el número de la última ruta del pedido encontrado
            ultima_ruta = ultimo_pedido.numero_ruta
            print(ultima_ruta)
            return Response({'numero_ruta': ultima_ruta, 'base':ultima_base}, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error obteniendo la última ruta:", str(e))
            return Response({'error': 'Ocurrió un error al obtener la última ruta'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
    @action(detail=False, methods=['PUT'])
    def actualizar_pedido(self, request):
        try:
            # Extraer los datos del request
            id_pedido = request.data.get('id')
            campo = request.data.get('campo')
            nuevo_dato = request.data.get('dato')
            usuario = request.data.get('usuario')
            documento = request.data.get('documento')
            efectivo = request.data.get('efectivo')
            numeroRuta = request.data.get('numeroRuta')

            print(campo, documento, nuevo_dato, id_pedido)
            # Validar que se hayan proporcionado todos los datos necesarios
            if not id_pedido or not campo or nuevo_dato is None:
                return Response({'error': 'ID del pedido, campo y dato son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

            # Obtener el pedido a actualizar
            pedido = Pedido.objects.filter(id=id_pedido).first()
            if not pedido:
                return Response({'error': 'Pedido no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            # Verificar si el campo proporcionado existe en el modelo
            if not hasattr(pedido, campo):
                return Response({'error': f'Campo {campo} no válido.'}, status=status.HTTP_400_BAD_REQUEST)

            # Si efectivo es True y hay un numeroRuta, actualizar todos los pedidos de esa ruta
            if efectivo and numeroRuta:
                hoy = datetime.now()
                pedidos_ruta = Pedido.objects.filter(
                    numero_ruta=numeroRuta,
                    documento=documento,
                    fecha__date=hoy
                )
                numero_pedidos = pedidos_ruta.count()
                if numero_pedidos == 0:
                        return Response({'error': 'No hay pedidos para esta ruta y entregador en el día de hoy.'}, status=status.HTTP_404_NOT_FOUND)

                 # Si 'efectivo' es True y 'campo' es 'base', actualizar todos los pedidos de esa ruta
                if campo == 'base' :
                    # Contar el número de pedidos en la ruta
                   
                    # Actualizar cada pedido con el valor dividido en el campo 'base'
                    pedidos_ruta.update(base=nuevo_dato)
                    # Crear registros para cada pedido actualizado
                    entregador = Entregador.objects.filter(documento=documento).first()
                    if entregador:
                        for pedido in pedidos_ruta:
                            Registros_Pedidos.objects.create(
                                documento=entregador,
                                nombre_responsable=usuario,
                                tipo_registro='Actualizacion',
                                descripcion_registro=f'Se actualizó el campo base en pedido {pedido.id}: nuevo dato "{nuevo_dato}"'
                            )

                    return Response({'success': f'La base de la ruta {numeroRuta} fue actualizada correctamente.'}, status=status.HTTP_200_OK)
                # Dividir el nuevo dato entre el número de pedidos
                nuevo_valor = float(nuevo_dato) / numero_pedidos

                # Actualizar cada pedido con el valor dividido
                pedidos_ruta.update(**{campo: nuevo_valor})

                # Crear registros para cada pedido actualizado
                entregador = Entregador.objects.filter(documento=documento).first()
                if entregador:
                    for pedido in pedidos_ruta:
                        Registros_Pedidos.objects.create(
                            documento=entregador,
                            nombre_responsable=usuario,
                            tipo_registro='Actualizacion',
                            descripcion_registro=f'Se actualizó {campo} en pedido {pedido.id}: nuevo dato "{nuevo_valor}"'
                        )

                return Response({'success': f'Todos los pedidos en la ruta {numeroRuta} actualizados correctamente.'}, status=status.HTTP_200_OK)

            # Obtener el dato antiguo antes de actualizar
            dato_viejo = getattr(pedido, campo)

            # Convertir el nuevo dato al tipo adecuado
            field = Pedido._meta.get_field(campo)
            if isinstance(field, models.BooleanField):
                nuevo_dato = nuevo_dato in ['True', 'true', True]
            elif isinstance(field, models.DecimalField):
                try:
                    nuevo_dato = float(nuevo_dato)
                except ValueError:
                    return Response({'error': 'El valor proporcionado debe ser un número decimal.'}, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar el campo dinámicamente para un solo pedido
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
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
    
    @action(detail=False, methods=['PUT'])
    def completar_ruta(self, request):
            try:
                # Extraer los datos del request
                id_ruta = request.data.get('ruta')
                usuario = request.data.get('usuario')
                documento = request.data.get('documento')

                # Validar que se hayan proporcionado todos los datos necesarios
                if not id_ruta or not usuario or not documento:
                    return Response(
                        {'error': 'Ruta, usuario y documento son requeridos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Obtener la fecha actual
                hoy = datetime.now().date()

                # Buscar el entregador por documento
                entregador = Entregador.objects.filter(documento=documento).first()
                if not entregador:
                    return Response(
                        {'error': 'No se encontró un entregador con el documento proporcionado.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Filtrar los pedidos de hoy que coincidan con el número de ruta y el entregador
                pedidos_a_completar = Pedido.objects.filter(
                    fecha__date=hoy,
                    numero_ruta=id_ruta,
                    completado=False,
                    documento=entregador.documento  # Filtra también por documento del entregador
                )

                if not pedidos_a_completar.exists():
                    return Response(
                        {'error': 'No se encontraron pedidos para la ruta especificada, entregador y el día de hoy.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Actualizar el campo completado a True para todos los pedidos filtrados
                pedidos_actualizados = pedidos_a_completar.update(completado=True)

                # Crear registro de la operación
                Registros_Pedidos.objects.create(
                    documento=entregador,
                    nombre_responsable=usuario,
                    tipo_registro='Actualizacion',
                    descripcion_registro=f'Se completaron {pedidos_actualizados} pedidos para la ruta "{id_ruta}" el {hoy}.'
                )

                return Response(
                    {'success': f'{pedidos_actualizados} pedidos completados correctamente.'},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                print("Error actualizando los pedidos", str(e))
                return Response(
                    {'error': f'Se produjo un error al completar los pedidos: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    @action(detail=False, methods=['GET'])
    def historico_entregadores(self, request):
        try:
            # Obtener el rango de fechas del request
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            fecha = request.query_params.get('fecha')
            
            hoy = datetime.now().date()
            
            # Determinar el rango de fechas
            if fecha:
                fecha_filtro = datetime.strptime(fecha, '%Y-%m-%d').date()
                pedidos = Pedido.objects.filter(fecha__date=fecha_filtro)
                rango_fechas = {'fecha_inicio': fecha_filtro, 'fecha_fin': fecha_filtro}
            elif fecha_inicio and fecha_fin:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                pedidos = Pedido.objects.filter(fecha__date__range=[fecha_inicio, fecha_fin])
                rango_fechas = {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}
            else:
                primer_dia_mes = hoy.replace(day=1)
                ultimo_dia_mes = (primer_dia_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                pedidos = Pedido.objects.filter(fecha__date__range=[primer_dia_mes, ultimo_dia_mes])
                rango_fechas = {'fecha_inicio': primer_dia_mes, 'fecha_fin': ultimo_dia_mes}

            # Filtrar y agrupar los pedidos por entregador
            entregadores_con_pedidos = pedidos.values('documento').annotate(
                total_pedidos=Count('id'),
                mayoristas=Count('id', filter=Q(tipo_pedido='Mayorista')),
                tiendas=Count('id', filter=Q(tipo_pedido='Tienda')),
                acompanado=Count('id', filter=Q(acompanado=True)),
                total_valor_pedido=Sum('valor_pedido'),
                valor_mayoristas=Sum('valor_pedido', filter=Q(tipo_pedido='Mayorista')),
                valor_tiendas=Sum('valor_pedido', filter=Q(tipo_pedido='Tienda')),
            )
            
            # Obtener los entregadores y añadir las estadísticas de pedidos
            documentos = [e['documento'] for e in entregadores_con_pedidos]
            entregadores = Entregador.objects.filter(documento__in=documentos)
            entregador_dict = {e.documento: e for e in entregadores}

            data = []
            for stats in entregadores_con_pedidos:
                entregador = entregador_dict.get(stats['documento'])
                if entregador:
                    data.append({
                        'documento': entregador.documento,
                        'entregador': f"{entregador.nombres} {entregador.apellidos}",
                        'total_pedidos': stats['total_pedidos'],
                        'mayoristas': stats['mayoristas'],
                        'tiendas': stats['tiendas'],
                        'acompanado': stats['acompanado'],
                        'total_valor': stats['total_valor_pedido'],
                        'valor_mayoristas': stats['valor_mayoristas'],
                        'valor_tiendas': stats['valor_tiendas'],
                    })

 # Incluir el rango de fechas en la respuesta
            response_data = {
            'rango_fechas': rango_fechas,
            'data': data
        }
            return Response(response_data)
        except Exception as e:
            print("Error obteniendo el log", str(e))
            return Response({'error': f'Se produjo un error al obtener los registros de entregadores: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['GET'])
    def estadisticas_pedidos(self, request):
        try:
            # Obtener la fecha actual y el primer día del mes
            hoy = datetime.now()
            primer_dia_mes = hoy.replace(day=1)

            # Agrupar los pedidos por fecha (día) en el mes actual y sumar el valor de los pedidos por día
            pedidos_por_dia = Pedido.objects.filter(fecha__date__gte=primer_dia_mes, fecha__date__lte=hoy) \
                .annotate(dia=TruncDate('fecha')) \
                .values('dia') \
                .annotate(total_pedido_dia=Sum('valor_pedido')) \
                .order_by('dia')

            # Obtener el top de pedidos por entregador en el mes actual
            top_pedidos_entregador = Pedido.objects.filter(fecha__date__gte=primer_dia_mes, fecha__date__lte=hoy) \
                .values('documento__nombres') \
                .annotate(total=Count('id')) \
                .order_by('-total')[:5]

            # Valor total de pedidos mayoristas en el mes actual
            total_mayoristas_mes = Pedido.objects.filter(tipo_pedido='Mayorista', fecha__date__gte=primer_dia_mes, fecha__date__lte=hoy) \
                .aggregate(Sum('valor_pedido'))['valor_pedido__sum'] or 0

            # Valor total de pedidos tienda en el mes actual
            total_tienda_mes = Pedido.objects.filter(tipo_pedido='Tienda', fecha__date__gte=primer_dia_mes, fecha__date__lte=hoy) \
                .aggregate(Sum('valor_pedido'))['valor_pedido__sum'] or 0

            # Convertir los resultados de pedidos por día en un formato adecuado para graficar
            pedidos_dia = [{'fecha': p['dia'], 'total': p['total_pedido_dia']} for p in pedidos_por_dia]

            # Construir la respuesta
            response_data = {
                'pedidos_por_dia': pedidos_dia,
                'top_pedidos_entregador': list(top_pedidos_entregador),
                'total_mayoristas_mes': total_mayoristas_mes,
                'total_tienda_mes': total_tienda_mes,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)