logger_config = {
    'version': 1, 
    'disable_existing_loggers': False,

    'formatters': {
        'file_format': {
            'format': '{asctime}:[{levelname}] - {name} | {message}',
            'style': '{'
        },
        'std_format':{
            'format': '[{levelname}] {message} || By {name}',
            'style': '{'
        }
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'std_format',
        },
        'file':{
            'class': 'logging.FileHandler',
            'filename': 'logs.log',
            'level':'INFO',
            'formatter':'file_format',
        }
    },

    'loggers': {
        'logger': {
            'level': 'DEBUG',
            'handlers':['console','file',]
        }
    },

}