from collections import namedtuple

import requests

TRACKING_URI = 'https://www.google-analytics.com/collect'


def report(tracking_id, client_id, requestable):
    for payload in requestable:
        data = {'v': '1', 'tid': tracking_id, 'cid': client_id, 'aip': '1'}
        data.update(payload)
        r = requests.post(TRACKING_URI, data=data)
        print r.request.body


class Requestable(object):

    def get_payload(self):
        raise NotImplementedError()

    def __iter__(self):
        yield self.get_payload()


class PageView(
        Requestable,
        namedtuple('PageView',
                   'location host_name path title referrer')):

    def __new__(cls, location=None, host_name=None, path=None, title=None,
                referrer=None):
        return super(PageView, cls).__new__(cls, location, host_name, path,
                                            title, referrer)

    def get_payload(self):
        payload = {'t': 'pageview'}
        if self.location:
            payload['dl'] = self.location
        if self.host_name:
            payload['dh'] = self.host_name
        if self.path:
            payload['dp'] = self.path
        if self.title:
            payload['dt'] = self.title
        if self.referrer:
            payload['dr'] = self.referrer
        return payload


class Event(Requestable, namedtuple('Event', 'category action label value')):

    def __new__(cls, category, action, label=None, value=None):
        return super(Event, cls).__new__(cls, category, action, label, value)

    def get_payload(self):
        payload = {'t': 'event', 'ec': self.category, 'ea': self.action}
        if self.label:
            payload['el'] = self.label
        if self.value:
            payload['ev'] = int(self.value)
        return payload


class Transaction(
        Requestable,
        namedtuple('Transaction',
                   'transaction_id items revenue tax shipping affiliation')):

    def __new__(cls, transaction_id, items, revenue=None, tax=None,
                shipping=None, affiliation=None):
        return super(Transaction, cls).__new__(
            cls, transaction_id, items, revenue, tax, shipping, affiliation)

    def get_payload(self):
        payload = {'t': 'transaction', 'ti': self.transaction_id}
        if self.affiliation:
            payload['ta'] = self.affiliation
        currencies = set()
        if self.revenue:
            payload['tr'] = str(self.revenue.net)
            currencies.add(self.revenue.currency)
        if self.tax:
            payload['tt'] = str(self.tax.net)
            currencies.add(self.tax.currency)
        if self.shipping:
            payload['ts'] = str(self.shipping.gross)
            currencies.add(self.shipping.currency)
        if currencies:
            if len(currencies) > 1:
                raise ValueError('All prices must use the same currency')
            (payload['cu'],) = currencies
        return payload

    def __iter__(self):
        yield self.get_payload()
        for i in self.items:
            yield i.get_payload_for_transaction(self.transaction_id)


class Item(namedtuple('Item', 'name unit_price quantity item_id category')):

    def __new__(cls, name, unit_price, quantity=None, item_id=None,
                category=None):
        return super(Item, cls).__new__(cls, name, unit_price, quantity,
                                        item_id, category)

    def get_payload_for_transaction(self, transaction_id):
        payload = {'t': 'item', 'ti': transaction_id, 'in': self.name}
        if self.unit_price:
            payload['ip'] = str(self.unit_price.gross)
            payload['cu'] = self.unit_price.currency
        if self.quantity:
            payload['iq'] = int(self.quantity)
        if self.item_id:
            payload['ic'] = self.item_id
        if self.category:
            payload['iv'] = self.category
        return payload
