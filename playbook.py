from core import plugin, model

class _playbook(plugin._plugin):
    version = 0.4

    def install(self):
        # Register models
        model.registerModel("playbook","_playbook","_document","plugins.playbook.models.playbook",True)
        model.registerModel("playbookStart","_playbookStart","_action","plugins.playbook.models.action")
        model.registerModel("playbookEnd","_playbookEnd","_action","plugins.playbook.models.action")
        model.registerModel("playbookSearch","_playbookSearch","_action","plugins.playbook.models.trigger")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("playbook","_playbook","_document","plugins.playbook.models.playbook")
        model.deregisterModel("playbookStart","_playbookStart","_action","plugins.playbook.models.action")
        model.deregisterModel("playbookEnd","_playbookEnd","_action","plugins.playbook.models.action")
        model.deregisterModel("playbookSearch","_playbookSearch","_action","plugins.playbook.models.trigger")

        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.4:
            model.registerModel("playbookSearch","_playbookSearch","_action","plugins.playbook.models.trigger")
