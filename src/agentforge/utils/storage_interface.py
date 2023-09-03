import uuid
from ..config import Config
from .chroma_utils import ChromaUtils


def metadata_builder(collection_name, name, details):
    if collection_name == 'Tasks':
        metadata = {
            "Status": "not completed",
            "Description": details,
            "List_ID": str(uuid.uuid4()),
            "Order": name + 1
        }

    if collection_name == 'Tools':
        metadata = {
            'Name': name,
            'Args': details['Args'],
            'Command': details['Command'],
            'Description': details['Description'],
            'Example': details['Example'],
            'Instruction': details['Instruction']
        }

    if collection_name == 'Actions':
        metadata = {
            'Name': name,
            'Description': details['Description'],
            'Example': details['Example'],
            'Instruction': details['Instruction'],
            'Tools': ', '.join(details['Tools'])
        }

    return metadata


def description_extractor(metadata):
    return metadata["Description"]


def id_generator(data):
    return [str(i + 1) for i in range(len(data))]


class StorageInterface:
    _instance = None
    storage_utils = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls.config = Config()
            cls._instance = super(StorageInterface, cls).__new__(cls, *args, **kwargs)
            cls._instance.initialize_storage()
        return cls._instance

    def __init__(self):
        # Add your initialization code here
        pass

    def initialize_chroma(self):
        self.storage_utils = ChromaUtils()
        self.storage_utils.init_storage()

        if self.config.get('ChromaDB', 'DBFreshStart') == 'True':
            self.storage_utils.reset_memory()
            storage = self.config.persona['Storage']

            [self.prefill_storage(key, value) for key, value in storage.items()]

    def initialize_storage(self):
        if self.storage_utils is None:
            storage_api = self.config.storage_api()
            if storage_api == 'chroma':
                self.initialize_chroma()
            else:
                raise ValueError(f"Unsupported Storage API library: {storage_api}")

    def prefill_storage(self, storage, data):
        """
        Initializes a collection with provided data source and metadata builder.
        """

        if not data:
            data = self.config.get_config_element(storage)

            if data == 'Invalid case':
                return

        collection_name = storage
        builder = metadata_builder
        extractor = description_extractor
        generator = id_generator
        ids = generator(data)

        if isinstance(data, list):
            metadatas = [builder(collection_name, i, item) for i, item in enumerate(data)]
        else:
            metadatas = [builder(collection_name, key, value) for key, value in data.items()]

        description = [extractor(metadata) for metadata in metadatas]

        save_params = {
            "collection_name": collection_name,
            "ids": ids,
            "data": description,
            "metadata": metadatas,
        }

        self.storage_utils.select_collection(collection_name)
        self.storage_utils.save_memory(save_params)
