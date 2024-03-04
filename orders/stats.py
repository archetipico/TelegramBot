from io import BytesIO
from matplotlib.pyplot import subplots_adjust, subplots, tight_layout
from numpy import arange
from pandas import DataFrame, DateOffset, Grouper, read_csv, Timestamp, to_datetime


class Stats:
    def __init__(self, msg, wd):
        self.msg = msg
        self.args = msg.text.split(' ')
        self.user = self.msg.from_user.id
        self.fp = '{}/orders/utility/usage.csv'.format(wd)

        self.result = {
            'type': 'photo',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return statistics
    def get(self) -> dict:
        if len(self.args) != 1 and len(self.args) != 2:
            self.result['type'] = 'text'
            self.result['send'] = 'Wrong command, type <code>stats</code>'
            self.result['status'] = False
            return self.result

        try:
            with open(self.fp, 'r') as f:
                df = read_csv(f, sep=';')

            if len(self.args) == 2 and self.args[1] == 'self':
                df = df[df['USER'] == self.user]

            # Success - Failure data
            succ = df[df['OUT'] == True]['CMD'].value_counts(ascending=True)
            fail = df[df['OUT'] == False]['CMD'].value_counts(ascending=True)
            succ_fail = DataFrame({'Passato': succ, 'Fallito': fail}, index=succ.index)
            # Create the first plot
            fig, (ax1, ax2) = subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]}, figsize=(16, 12))
            succ_fail.plot.barh(ax=ax1, grid=True)
            ax1.set_title('Total calls', fontsize=22)
            ax1.set_xlabel('')
            ax1.set_ylabel('')
            ax1.legend(fontsize=12)

            # Weekly data
            df['TIME'] = to_datetime(df['TIME'], unit='s')
            start_date = Timestamp.now().normalize() - DateOffset(weeks=1)
            df = df[df['TIME'] >= start_date]
            time_data = df.groupby(Grouper(key='TIME', freq='D')).size()
            time_data = time_data.reset_index()
            time_values = arange(len(time_data))
            cmds = time_data.columns[1:]
            # Iterate through each CMD and plot the ridge plot
            for i, cmd in enumerate(cmds):
                values = time_data[cmd]
                ax2.fill_between(time_values, values + i, label=cmd, alpha=0.7)
            ax2.set_title('Last week calls', fontsize=22)
            ax2.set_xlabel('')
            ax2.set_ylabel('')
            ax2.set_xticks(time_values)
            ax2.set_xticklabels(time_data['TIME'].dt.strftime('%d-%m'), rotation=45)

            # Adjust layout
            tight_layout()
            subplots_adjust(hspace=0.3)

            # Save the plot
            output = BytesIO()
            fig.savefig(output, format='png', bbox_inches='tight')

            self.result['send'] = output.getvalue()
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = str(e)
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
