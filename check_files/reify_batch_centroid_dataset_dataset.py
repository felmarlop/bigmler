from bigml.api import BigML
api = BigML()

source1 = api.create_source("iris.csv")
api.ok(source1)

dataset1 = api.create_dataset(source1, \
    {'name': u'iris'})
api.ok(dataset1)

cluster1 = api.create_cluster(dataset1, \
    {'name': u'iris'})
api.ok(cluster1)

batchcentroid1 = api.create_batch_centroid(cluster1, dataset1, \
    {'name': u'iris dataset with iris', 'output_dataset': True})
api.ok(batchcentroid1)

dataset2 = api.get_dataset(batchcentroid1['object']['output_dataset_resource'])
api.ok(dataset2)

dataset2 = api.update_dataset(dataset2, \
    {'name': u'iris dataset with iris'})
api.ok(dataset2)

dataset3 = api.create_dataset(dataset2, \
    {'name': u'my_dataset_from_dataset_from_batch_centroid_name',
     'new_fields': [{'field': u'( integer ( replace ( field "cluster" ) "Cluster " "" ) )',
                     u'name': u'Cluster'}]
     'objective_field': {'id': u'100000'}})
api.ok(dataset3)
