from __future__ import (absolute_import, division, print_function)
from couchdb import Server
from couchdb.design import ViewDefinition

class Database(object):
    """ TODO: docstring
    """
    def __init__(self, server_url=u'http://127.0.0.1:5984/', db_name='ble-new'):
        # 'http://dfki-1239.dfki.uni-kl.de:5984/'
        self.server_url, self.db_name = server_url, db_name
        self.couch = Server(self.server_url)
        self.db = self.couch[self.db_name]

    def __getitem__(self, doc_id):
        """ returns the database document
        """
        return self.db[doc_id]

    def _sync_permanent_views(self):
        view = ViewDefinition('elvis', 
            'newest_location_documents_from_elvis', '''
                function(doc) {
                    if (doc.source && doc.source == "elvis" && doc.location) 
                        emit(doc.dest, doc.location.positions[0].timestamp);
                }''',
                '''
                function(keys, values, rereduce) {
                    if (rereduce) {

                        var result = {
                            id: 'fffaef464c42c6ffe0285be3d7da3684',
                            timestamp: '2113-08-04 19:09:24:089'
                        };

                        return (result);
                    } else {
                        
                        var result = {
                            id: keys[0][1],
                            timestamp: values[0]
                        };
                
                        for (var i = 1, e = keys.length; i < e; ++i) {
                            if (values[i] > result.timestamp) {
                                result.timestamp = values[i];
                                result.id = keys[i][1];
                            }
                        }

                        return (result);
                    }
                }'''              
        )
        view.sync(self.db)

        view = ViewDefinition('elvis', 'all_location_documents_from_elvis', '''
            function(doc) {
                if (doc.source && doc.source == "elvis" && doc.location) 
                    emit([doc.location.positions[doc.location.positions.length-1].timestamp, doc.dest]);
            }'''
        )
        view.sync(self.db)

        view = ViewDefinition('elvis', 'all_ble_documents', '''
            function(doc) {
                if (doc.ble) 
                    emit([doc.ble[doc.ble.length-1].timestamp, doc.source]);
            }'''
        )
        view.sync(self.db)

        view = ViewDefinition('elvis', "all_location_documents_from_reckonme", '''
            function(doc) {
                if (doc.dest && doc.source && doc.timestamp && doc.location && doc.dest == 'elvis') {
                    emit([doc.timestamp, doc.source])
                }
            }'''
        )
        view.sync(self.db)

    def view_result(self, view_str):
        """ returns a representation of a parameterized view 
        (either permanent or temporary) 
        """
        return self.db.view("_design/elvis/_view/" + view_str)


def test():
    db = Database()
    db._sync_permanent_views()
    print(len(list(db.view_result(u'all_location_documents_from_reckonme'))))
    for row in db.view_result('all_location_documents_from_reckonme'):
        print(row.id)
        print(db[row.id])
        break


if __name__ == '__main__':
    test()