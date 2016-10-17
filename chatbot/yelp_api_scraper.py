from yelp.client import Client
import time
from decimal import Decimal
import conf

NULL = 'NONE'

yelp_client = Client(conf.auth)

limit = 10
offset = 0


def fetch_restaurants(location):

    params = {
        'term': 'restaurant',
        'limit': limit,
        'sort': 2,
        'offset': offset
    }

    print 'fetch_restaurant'
    print params

    resp = yelp_client.search(location, **params)
    print resp.total
    print resp.businesses
    while len(resp.businesses) > 0:
        # print(map(lambda b: b.name, resp.businesses))
        store_businesses(resp.businesses, location)
        params['offset'] += limit
        try:
            print params
            resp = yelp_client.search(location, **params)
            print resp
        except Exception, e:
            print 'yelp_error: %s' % e
            break  # PE should be done


def store_businesses(businesses, location):
    batch_list = [{'PutRequest': {'Item': clean_meta(serialize_business(b, location))}}
                  for b in filter_closed(businesses)]
    # print(batch_list)
    __store_businesses(batch_list, 1)


def __store_businesses(batch_list, backoff):
    resp = conf.aws_dynamo_db.batch_write_item(RequestItems={conf.RESTAURANT_TABLE: batch_list})
    if conf.RESTAURANT_TABLE in resp['UnprocessedItems'] and len(resp['UnprocessedItems'][conf.RESTAURANT_TABLE]) > 0:
        time.sleep(backoff)
        __store_businesses(resp['UnprocessedItems'][conf.RESTAURANT_TABLE], backoff * 2)


def filter_closed(businesses):
    return filter(lambda business: business.is_closed is not True, businesses)


def serialize_business(business, location):
    return {
        'Location': location,
        'Yelp_id': business.id,
        'categories': [{'alias': c.alias, 'name': c.name} for c in business.categories],
        'display_phone': business.display_phone,
        'eat24_url': business.eat24_url if __has('eat24_url', business) else '',
        'image_url': business.image_url,
        'is_claimed': int(business.is_claimed),
        'location': {
            'city': business.location.city,
            'state_code': business.location.state_code,
            'postal_code': business.location.postal_code,
            'country_code': business.location.country_code,
            'cross_streets': business.location.cross_streets if __has('cross_streets', business.location) else [],
            'neighborhoods': business.location.neighborhoods,
            'coordinate': {
                'lat': business.location.coordinate.latitude,
                'lng': business.location.coordinate.longitude
            } if __has('coordinate', business.location) else {}
        },
        'menu_date_updated': Decimal(business.menu_date_updated) if __has('menu_date_updated', business) else '',
        'menu_provider': business.menu_provider if __has('menu_provider', business) else '',
        'mobile_url': business.mobile_url,
        'name': business.name,
        'phone': business.phone,
        'rating': Decimal(business.rating),
        'rating_img_url': business.rating_img_url,
        'rating_img_url_small': business.rating_img_url_small,
        'rating_img_url_large': business.rating_img_url_large,
        'reservation_url': business.reservation_url if __has('reservation_url', business) else '',
        'snippet_image_url': business.snippet_image_url,
        'snippet_text': business.snippet_text,
        'url': business.url
    }


def clean_meta(meta):
    if type(meta) is dict:
        for key, val in meta.items():
            if type(val) is dict:
                meta[key] = clean_meta(val)
            else:
                meta[key] = clean(val)

        return meta
    else:
        return clean(meta)


def clean(val):
    if type(val) is list:
        new_val = []
        for v in val:
            new_val.append(clean_meta(v))
        return new_val
    elif val == '0' or val == '1':
        return int(val)
    elif type(val) is float:
        return Decimal(str(val))
    elif val == '':
        return NULL
    else:
        return val


def __has(field, obj):
    try:
        attr = getattr(obj, field)
    except AttributeError:
        return False

    return (attr is not None)


# if __name__ == "__main__":
#     fetch_restaurants('San Francisco')
#
