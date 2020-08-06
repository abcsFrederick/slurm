import events from 'girder/events';
import router from 'girder/router';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';

import ConfigView from './views/configuration/configView';

exposePluginConfig('Slurm', 'plugins/Slurm/config');
router.route('plugins/Slurm/config', 'SlurmConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});