
from optparse import OptionParser

from bottle import run

from .kule import Kule


def main():
    parser = OptionParser()
    parser.add_option("--bind", dest="address",
                      help="Binds an address to kule")
    parser.add_option("--mongodb-host", dest="mongodb_host",
                      help="MongoDB host")
    parser.add_option("--mongodb-port", dest="mongodb_port",
                      help="MongoDB port")
    parser.add_option("-d", "--database", dest="database",
                      help="MongoDB database name")
    parser.add_option("-c", "--collections", dest="collections",
                      help="Comma-separated collections.")
    parser.add_option("-k", "--klass", dest="klass",
                      help="Kule class")
    # add help...
    options, args = parser.parse_args()
    collections = (options.collections or "").split(",")
    database = options.database
    mongodb_port = int(options.mongodb_port or "27017")
    if not database:
        parser.error("MongoDB database not given.")
    host, port = (options.address or 'localhost'), 8000
    if ':' in host:
        host, port = host.rsplit(':', 1)

    if options.klass is None:
        klass = Kule
    try:
        klass = __import__(options.klass, fromlist=['kule']).kule
    except AttributeError:
        raise ImportError('Bad kule module.')
    except TypeError:
        klass = Kule

    kule = klass(
        host=options.mongodb_host,
        port=mongodb_port,
        database=options.database,
        collections=collections
    )
    run(host=host, port=port, app=kule.get_bottle_app())

if __name__ == '__main__':
    main()
