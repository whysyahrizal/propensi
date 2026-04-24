# Recovery: 0001 used to be SeparateDatabaseAndState with empty
# database_operations, so `schedules.0001_initial` could be applied with no
# tables. Create missing tables for those DBs. No-op if they already exist.

from django.db import migrations


def _forwards(apps, schema_editor):
    ShiftSchedule = apps.get_model("schedules", "ShiftSchedule")
    ShiftSchedulePersonnel = apps.get_model("schedules", "ShiftSchedulePersonnel")
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))

    t1 = ShiftSchedule._meta.db_table
    t2 = ShiftSchedulePersonnel._meta.db_table
    if t1 not in tables:
        schema_editor.create_model(ShiftSchedule)
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
    if t2 not in tables:
        schema_editor.create_model(ShiftSchedulePersonnel)


def _backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("schedules", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_forwards, _backwards),
    ]
