
def migrate(migrator, database, fake=False, **kwargs):
    migrator.sql('DROP INDEX IF EXISTS "jointlimit_name"')


def rollback(migrator, database, fake=False, **kwargs):
    migrator.sql(
        'CREATE UNIQUE INDEX IF NOT EXISTS "jointlimit_name" ON "joint_limits" ("name")'
    )
