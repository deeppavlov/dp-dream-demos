#!/usr/bin/env python
import asyncio
import logging
from typing import Callable, Dict

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {'Content-Type': 'application/json;charset=utf-8'}


