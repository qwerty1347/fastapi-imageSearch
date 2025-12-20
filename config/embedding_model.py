class EmbeddingModel:
    MODELS = {
        'hugging_face': {
            'clip' : {
                'ViT-B-32': {
                    'name': 'clip-ViT-B-32',
                    'size': 512,
                    'distance': 'Cosine'
                },
                'ViT-L-14': {
                    'name': 'clip-ViT-L-14',
                    'size': 768,
                    'distance': 'Cosine'
                },
            }
        }
    }