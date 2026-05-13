import csv

import pytest
from allocation import config
import requests
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
from pathlib import Path
from ..random_refs import (random_batch_ref,
                           random_sku,
                           random_order_id)


def run_cli_script(folder):
    """a bit of python import hackery to load the script and run its main()"""
    path = Path(__file__).parent / "../../src/bin/allocate-from-csv"
    spec = spec_from_loader("script", SourceFileLoader("script", str(path)))
    script = module_from_spec(spec)
    spec.loader.exec_module(script)
    script.main(folder)


def test_app_reads_csv_with_batches_and_orders(make_csv):
    sku1, sku2 = random_sku('s1'), random_sku('s2')
    batch1, batch2, batch3 = (random_batch_ref('b1'),
                              random_batch_ref('b2'),
                              random_batch_ref('b3'))
    order_id = random_order_id('o')
    make_csv('batches.csv', [
        ['batch_ref', 'sku', 'quantity', 'eta'],
        [batch1, sku1, 100, ''],
        [batch2, sku2, 100, '2026-05-11'],
        [batch3, sku2, 100, '2026-05-12'],
    ])
    orders_csv = make_csv('orders.csv', [
        ['order_id', 'sku', 'quantity'],
        [order_id, sku1, 3],
        [order_id, sku2, 12],
    ])
    run_cli_script(orders_csv.parent)

    expected_output_csv = orders_csv.parent / 'allocations.csv'
    with open(expected_output_csv) as fcsv:
        rows = list(csv.reader(fcsv))
    assert rows == [
        ['order_id', 'sku', 'quantity', 'batch_ref'],
        [order_id, sku1, '3', batch1],
        [order_id, sku2, '12', batch2],
    ]
