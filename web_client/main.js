import './routes';

import { registerPluginNamespace } from 'girder/pluginUtils';

import * as Slurm from './index';

registerPluginNamespace('slurm', Slurm);
