import View from '@girder/core/views/View';
import slurmSelectionTemplate from '../../templates/widgets/slurmSelection.pug';
import { restRequest } from '@girder/core/rest';
import events from '@girder/core/events';

import '../../stylesheets/widgets/slurmSelection.styl';

var slurmSelection = View.extend({
    events: {
        'click #g-SlurmOption-settings-form': function (event) {
            event.preventDefault();
            this.$('#g-slurmOption-error-message').empty();
            this._saveSettings({
                'gres': this.$('#g-slurmOption-gres').val(),
                'partition': this.$('#g-slurmOption-partition').val(),
                'nodes': this.$('#g-slurmOption-nodes').val(),
                'ntasks': this.$('#g-slurmOption-ntasks').val(),
                'cpu_per_task': this.$('#g-slurmOption-cpu').val(),
                'mem_per_cpu': this.$('#g-slurmOption-mem').val(),
                'time': this.$('#g-slurmOption-time').val()
            });
        }
    },
    initialize: function () {
        slurmSelection.getSettings((settings) => {
            this.settings = settings;
            this.render();
        });
    },
    render: function () {
        this.$el.html(slurmSelectionTemplate({
            settings: this.settings
        }));
        return this;
    },
    _saveSettings: function (settings) {
        /* Now save the settings */
        return restRequest({
            type: 'PUT',
            url: 'slurm/slurmOption',
            data: settings,
            error: null
        }).done(() => {
            /* Clear the settings that may have been loaded. */
            slurmSelection.clearSettings();
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
    getSettings: function (callback) {
        if (!slurmSelection.settings) {
            restRequest({
                type: 'GET',
                url: 'slurm/slurmOption'
            }).done((resp) => {
                slurmSelection.settings = resp;
                if (callback) {
                    callback(slurmSelection.settings);
                }
            });
        } else {
            if (callback) {
                callback(slurmSelection.settings);
            }
        }
    },
    clearSettings: function () {
        delete slurmSelection.settings;
    }
});

export default slurmSelection;