# Generated by Django 5.0.6 on 2024-08-10 19:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registros_pedidos',
            old_name='numero_documento',
            new_name='documento',
        ),
        migrations.AlterField(
            model_name='registros_pedidos',
            name='tipo_registro',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre_entregador', models.CharField(max_length=100)),
                ('numero_ruta', models.CharField(max_length=50)),
                ('valor_pedido', models.DecimalField(decimal_places=2, max_digits=15)),
                ('numero_factura', models.CharField(max_length=50)),
                ('tipo_pedido', models.CharField(max_length=50)),
                ('tipo_vehiculo', models.CharField(max_length=50)),
                ('acompanado', models.BooleanField()),
                ('acompanante', models.CharField(blank=True, max_length=100, null=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('valor_transferencia', models.DecimalField(decimal_places=2, max_digits=10)),
                ('completado', models.BooleanField(default=False)),
                ('usuario', models.CharField(max_length=50)),
                ('documento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pedidos.entregador')),
            ],
            options={
                'db_table': 'pedido',
                'managed': True,
            },
        ),
    ]
