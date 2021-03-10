from core import plugin, model

class _playbook(plugin._plugin):
    version = 1.1

    def install(self):
        # Register models
        model.registerModel("playbook","_playbook","_document","plugins.playbook.models.playbook",True)
        model.registerModel("playbookStart","_playbookStart","_action","plugins.playbook.models.action")
        model.registerModel("playbookEnd","_playbookEnd","_action","plugins.playbook.models.action")
        model.registerModel("playbookSearch","_playbookSearch","_trigger","plugins.playbook.models.trigger")
        model.registerModel("playbookGet","_playbookGet","_action","plugins.playbook.models.action")
        model.registerModel("playbookUpdate","_playbookUpdate","_action","plugins.playbook.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("playbook","_playbook","_document","plugins.playbook.models.playbook")
        model.deregisterModel("playbookStart","_playbookStart","_action","plugins.playbook.models.action")
        model.deregisterModel("playbookEnd","_playbookEnd","_action","plugins.playbook.models.action")
        model.deregisterModel("playbookSearch","_playbookSearch","_action","plugins.playbook.models.trigger")
        model.deregisterModel("playbookGet","_playbookGet","_action","plugins.playbook.models.action")
        model.deregisterModel("playbookUpdate","_playbookUpdate","_action","plugins.playbook.models.action")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.4:
            model.registerModel("playbookSearch","_playbookSearch","_trigger","plugins.playbook.models.trigger")
        if self.version < 0.5:
            model.registerModel("playbookGet","_playbookGet","_action","plugins.playbook.models.action")
        if self.version < 1.1:
            model.registerModel("playbookUpdate","_playbookUpdate","_action","plugins.playbook.models.action")
        return True