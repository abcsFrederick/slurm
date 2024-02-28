import './routes';

import { registerPluginNamespace } from '@girder/core/pluginUtils';

import * as Slurm from './index';

registerPluginNamespace('slurm', Slurm);
