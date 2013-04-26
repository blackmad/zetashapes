from flask.ext.assets import ManageAssets
from flask.ext.script import Manager
from flask.ext.security.script import CreateUserCommand

from app import app

manager = Manager(app)
manager.add_command("assets", ManageAssets())
manager.add_command('create_user', CreateUserCommand())

if __name__ == "__main__":
    manager.run()
