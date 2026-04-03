import datetime
import logging

import param

log = logging.getLogger(f'tethys.{__name__}')


class NldasTimestepOptions(param.Parameterized):
    """
    Param form that defines the form in the NLDAS Timestep options step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_nldas_timestep_options()

    def set_nldas_timestep_options(self):
        self.param.add_parameter(
            'nldas_start_time',
            param.String(
                label='NLDAS Starting time',
                doc='Set the NLDAS starting time, in format YYYY-MM-DD',
                default='1979-01-01T13',
                allow_None=False
            )
        )
        dt_now = datetime.datetime.now()
        yesterday = dt_now - datetime.timedelta(days=1.0)
        yesterday_str = f'{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}'
        self.param.add_parameter(
            'nldas_end_time',
            param.String(
                label='NLDAS Ending time',
                doc='Set the NLDAS Ending time, in format YYYY-MM-DD, up to yesterday',
                default=yesterday_str,
                allow_None=False
            )
        )
