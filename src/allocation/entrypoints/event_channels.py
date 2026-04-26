from abc import ABC, abstractclassmethod
import json
import allocation.domain.commands as commands
import allocation.domain.events as events
from dataclasses import asdict

class Channel(ABC):
    channel_name: str

    @abstractclassmethod
    def format_as_chanel_message():
        pass


class ChannelAllocate(Channel):
    channel_name = "allocate"

    @classmethod
    def format_as_chanel_message(cls, order_id, sku, quantity):
        command = commands.Allocate(order_id, sku, quantity)
        return json.dumps(asdict(command))


class ChannelCreateBatch(Channel):
    channel_name = "create_batch"

    @classmethod
    def format_as_chanel_message(cls, reference, sku, quantity, eta = None):
        command = commands.CreateBatch(reference, sku, quantity, eta)
        return json.dumps(asdict(command))


class ChannelDeallocate(Channel):
    channel_name = "deallocate"

    @classmethod
    def format_as_chanel_message(cls, order_id, sku, quantity):
        command = commands.Deallocate(order_id, sku, quantity)
        return json.dumps(asdict(command))


class ChannelChangeBatchQuantity(Channel):
    channel_name = "change_batch_quantity"

    @classmethod
    def format_as_chanel_message(cls, batch_ref, quantity):
        command = commands.ChangeBatchQuantity(batch_ref, quantity)
        return json.dumps(asdict(command))


class ChannelEventConsumerPing(Channel):
    channel_name = "eventconsumer_ping"

    @classmethod
    def format_as_chanel_message(cls, sender_type):
        message_dict = {"sender_type": sender_type}
        return json.dumps(message_dict)


class ChannelEventConsumerOnline(Channel):
    channel_name = "eventconsumer_online"

    @classmethod
    def format_as_chanel_message(cls, sender_type):
        message_dict = {"sender_type": sender_type}
        return json.dumps(message_dict)
