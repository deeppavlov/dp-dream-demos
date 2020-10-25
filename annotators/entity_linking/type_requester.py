from typing import List, Optional
from logging import getLogger

import requests

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register('type_requester')
class TypeRequester(Component):
    def __init__(self, *args, **kwargs):
        pass

    def request_wikidata(self, id: str, type_id: bool=False) -> Optional[str]:
        ans = None
        try:
            resp = requests.get(f'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={id}', timeout=1)
            if resp.status_code == 200:
                if type_id:
                    ans = resp.json()['entities'][id]['labels']['en']['value']
                else:
                    ans = resp.json()['entities'][id]['claims']['P31'][0]['mainsnak']['datavalue']['value']['id']
        except requests.exceptions.ReadTimeout:
            log.warning(f'TimeoutError for {id}')
        except Exception as e:
            log.error(repr(e))
        finally:
            return ans

    def __call__(self, x: List[List[List[str]]]) -> List[List[List[Optional[str]]]]:
        ans = []
        for entity_ids in x[0]:
            buf = []
            for entity_id in entity_ids:
                type_id = self.request_wikidata(entity_id)
                buf.append(self.request_wikidata(type_id, True))
            ans.append(buf)
        return [ans]
