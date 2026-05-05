import json
import logging
import redis

from allocation import config, bootstrap
from allocation.domain import commands
from allocation.entrypoints.event_channels import (ChannelEventConsumerOnline,
                                                   ChannelChangeBatchQuantity,
                                                   ChannelEventConsumerPing)

logger = logging.getLogger(__name__)
ms = bootstrap.bootstrap()
r = redis.Redis(**config.get_redis_host_and_port())

def main():
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(
        (
            ChannelChangeBatchQuantity.channel_name,
            ChannelEventConsumerPing.channel_name
         )
    )
    for m in pubsub.listen():
        logging.debug("handling %s", m)
        m_channel = m["channel"].decode('utf-8')
        if m_channel == ChannelChangeBatchQuantity.channel_name:
            message_data_dict = json.loads(m["data"])
            handle_change_batch_quantity(message_data_dict)
        elif m_channel == ChannelEventConsumerPing.channel_name:
            r.publish(ChannelEventConsumerOnline.channel_name,
                      ChannelEventConsumerOnline.format_as_chanel_message("eventconsumer"))



def handle_change_batch_quantity(message_data):
    cmd = commands.ChangeBatchQuantity(reference=message_data["reference"],
                                       quantity=message_data["quantity"])
    ms.handle(cmd)


if __name__ == "__main__":
    main()