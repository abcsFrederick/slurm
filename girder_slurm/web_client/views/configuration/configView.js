import View from '@girder/core/views/View';

import PluginConfigBreadcrumbWidget from
    '@girder/core/views/widgets/PluginConfigBreadcrumbWidget';
import { restRequest } from '@girder/core/rest';
import events from '@girder/core/events';

import ConfigViewTemplate from '../../templates/configuration/configView.pug';
import '../../stylesheets/configuration/configView.styl';

// import 'bootstrap-switch'; // /dist/js/bootstrap-switch.js',
// import 'bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.css';

var ConfigView = View.extend({
    events: {
        'submit #g-Slurm-settings-form': function (event) {
            event.preventDefault();
            this.$('#g-Slurm-settings-error-message').empty();
            this._saveSettings([{
                key: 'slurm.SHARED_PARTITION',
                value: this.$('#g-Slurm-settings-SHARED').val()
            }, {
                key: 'slurm.CRONTAB_PARTITION',
                value: this.$('#g-Slurm-settings-CRONTAB').val()
            }, {
                key: 'slurm.API_URL',
                value: this.$('#g-Slurm-settings-API_URL').val()
            }, {
                key: 'slurm.PARTITION',
                value: this.$('#g-Slurm-settings-PARTITION').val()
            }, {
                key: 'slurm.NODES',
                value: this.$('#g-Slurm-settings-NODES').val()
            }, {
                key: 'slurm.TASKS',
                value: this.$('#g-Slurm-settings-TASKS').val()
            }, {
                key: 'slurm.CPU',
                value: this.$('#g-Slurm-settings-CPU').val()
            }, {
                key: 'slurm.MEMERY',
                value: this.$('#g-Slurm-settings-MEMERY').val()
            }, {
                key: 'slurm.TIME',
                value: this.$('#g-Slurm-settings-TIME').val()
            }]);
        }
    },

    initialize: function () {
        ConfigView.getSettings((settings) => {
            this.settings = settings;
            this.render();
        });
    },

    render: function () {
        console.log(this.settings)
        this.$el.html(ConfigViewTemplate({
            settings: this.settings
        }));

        if (!this.breadcrumb) {
            this.breadcrumb = new PluginConfigBreadcrumbWidget({
                pluginName: 'Slurm',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }

        // this.$('.g-SSR-task-switch').bootstrapSwitch()
        //     .off('switchChange.bootstrapSwitch')
        //     .on('switchChange.bootstrapSwitch', (event, state) => {
        //         var plugin = $(event.currentTarget).attr('key');

        //     });
        return this;
    },

    _saveSettings: function (settings) {
        /* Now save the settings */
        return restRequest({
            type: 'PUT',
            url: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(() => {
            /* Clear the settings that may have been loaded. */
            ConfigView.clearSettings();
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }).fail((resp) => {
            this.$('#g-Slurm-settings-error-message').text(
                resp.responseJSON.message
            );
        });
    }
}, {
    /**
     * Get settings if we haven't yet done so.  Either way, call a callback
     * when we have settings.
     *
     * @param {function} callback a function to call after the settings are
     *      fetched.  If the settings are already present, this is called
     *      without any delay.
     */
    getSettings: function (callback) {
        if (!ConfigView.settings) {
            restRequest({
                type: 'GET',
                url: 'slurm/settings'
            }).done((resp) => {
                ConfigView.settings = resp;
                if (callback) {
                    callback(ConfigView.settings);
                }
            });
        } else {
            if (callback) {
                callback(ConfigView.settings);
            }
        }
    },

    /**
     * Clear the settings so that getSettings will refetch them.
     */
    clearSettings: function () {
        delete ConfigView.settings;
    }
});

export default ConfigView;
