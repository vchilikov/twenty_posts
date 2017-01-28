from uuid import uuid4


class Messages(list):
    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = Messages()
        return cls.__instance

    def __init__(self):
        super(Messages, self).__init__()

    def append(self, text):
        super(Messages, self).append({'pk': str(uuid4()), 'text': text})
        while len(self) > 20:
            self.pop(0)

    def has_new_pk(self, message_pk):
        last_message_pk = self[-1]['pk'] if len(self) else ''
        return message_pk != last_message_pk
