import events from '@girder/core/events';
import router from '@girder/core/router';
import { exposePluginConfig } from '@girder/core/utilities/PluginUtils';

import ConfigView from './views/configuration/configView';

exposePluginConfig('slurm', 'plugins/slurm/config');
router.route('plugins/slurm/config', 'slurmConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});