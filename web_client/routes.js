import events from 'girder/events';
import router from 'girder/router';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';

import ConfigView from './views/configuration/configView';

exposePluginConfig('slurm', 'plugins/slurm/config');
router.route('plugins/slurm/config', 'slurmConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});