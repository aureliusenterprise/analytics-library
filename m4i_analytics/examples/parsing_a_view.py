import pandas as pd


def parse_view_concepts(model):
    views = model.views
    view_concepts = []
    for index, view in views.iterrows():
        view_desc= {'view_name':view['name'], 'view_id':view.id}
        if (view.nodes is not None) and (len(view.nodes)>0):
            res = parse_view_items(view.nodes, view_desc, {}, [], [], 0)        
            view_concepts = view_concepts+res
        if (view.connections is not None) and (len(view.connections)>0):
            res = parse_view_items(view.connections, view_desc, {}, [], [], 0)        
            view_concepts = view_concepts+res
    df_view_concepts = pd.DataFrame(view_concepts)
    return df_view_concepts
# END parse_view_concepts
    
def parse_view_items(items, view_desc, levels_, levels_arr, levels_ref, level_):
    res = []
    for item in items:
        levels_new = levels_.copy()
        item_keys = item.keys()
        id_ = ''
        x=0
        y=0
        w=0
        h=0
        label_=''
        type_=None
        ref=None
        ref_type=None
        source=None
        target=None
        res_new  = {}
        if '@x' in item_keys:
            x = item['@x']
        if '@y' in item_keys:
            y = item['@y']
        if '@w' in item_keys:
            w = item['@w']
        if '@h' in item_keys:
            h = item['@h']
        if '@identifier' in item_keys:
            id_ = item['@identifier']
        if '@elementRef' in item_keys:
            ref = item['@elementRef']
            ref_type='ar3_Element'
        if '@source' in item_keys:
            source = item['@source']
        if '@target' in item_keys:
            target = item['@target']
        if '@RelationshipRef' in item_keys:
            ref = item['@relationshipRef']
            ref_type='ar3_Relationship'
        if '@xsi_type' in item_keys:
            type_ = item['@xsi_type']
        if 'ar3_label' in item_keys:
            label_obj = item['ar3_label'][0]
            label_=label_obj['value']
        if 'ar3_viewRef' in item_keys:
            view_ref = item['ar3_viewRef'][0]
            if '@ref' in view_ref.keys():
                ref = view_ref['@ref']
                ref_type='ar3_viewRef'
            ref_type='ar3_view'
        if 'ar3_node' in item_keys:
            item_list = item['ar3_node']
            #list_ = []
            ref_type='ar3_node'
            #print(item_list)
            #for item_ in item_list:
            #    print(item_)
            levels_new['level'+str(level_)] = id_
            levels_arr_new = levels_arr.copy()
            levels_arr_new.append(id_)
            if ref !=None:
                levels_ref_new = levels_ref.copy()
                levels_ref_new.append(ref)
            else:
                levels_ref_new= levels_ref
            part = parse_view_items(item_list, view_desc, levels_new, levels_arr_new, levels_ref_new, level_+1)
            #    if isinstance(part, list):
            #        list_ = list_ + part
            #    else:
            #        list_.append(part)
            res = res+part
        res_new = {'x': x, 'y':y, 'w':w, 'h':h, 'id': id_, 'label':label_, 'type':type_, 'ref':ref, 'ref_type': ref_type, 
                   'levels_id':levels_arr, 'levels_ref':levels_ref, 'source':source, 'target':target}
        res_new.update(levels_)
        res_new.update(view_desc)
        res.append(res_new)
    return res

# END parse_view_items

if __name__ == '__main__': 

    model_options = {
                    'projectName': 'Archisurance', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    
    model = ArchimateUtils.load_model_from_repository(**model_options)    
    
    view_concepts = parse_view_concepts(model)
    
    data = view_concepts[view_concepts.type == 'ar3_Element']
    data = data[data.levels_ref.apply(lambda x: len(x))>0]
    data = data[data.ref_type == 'ar3_Element']
    data = data[['levels_ref','ref','view_name','view_id','id']]
    
    rows=[]
    t= data.apply(lambda row: [rows.append({'ref':row['ref'], 'levels_ref':nn}) for nn in row['levels_ref']], axis=1)
    data1=pd.DataFrame(rows)
    data2 = data.merge(data1, how='left', on='ref')
    data2 = data2[['levels_ref_y','ref','view_name','view_id','id']]
    data2.columns=['levels_ref','ref','view_name','view_id','id']
    data2 = data2.drop_duplicates()
    
    data4 = data2.merge(model.edges, how='left', left_on='ref', right_on='source')
    data4 = data4[['levels_ref','ref','view_name','view_id','id_x','target']]
    data4.columns = ['levels_ref','ref','view_name','view_id','id','rel']
    
    data3 = data2.merge(model.edges, how='left', left_on='ref', right_on='target')
    data3 = data3[['levels_ref','ref','view_name','view_id','id_x','source']]
    data3.columns = ['levels_ref','ref','view_name','view_id','id','rel']
    data3 = pd.concat([data4,data3])
    data3 = data3.fillna('missing')
    
    data3['comparison'] = data3.apply(lambda x: x.rel == x.levels_ref, axis=1)
    data4 = data3[data3.comparison==True]
    # all nested concepts, which have also corresponding relationships in the model
    l = list(data4.id)
    # investigate the type of relationships
    data5 = data2[data2.id.isin( l)]
    data6 = model.edges
    res = []
    
    data7 = data6['type'].apply(lambda d: d['tag'])
    
    t = [res.append((n.ref, dict(nn)['tag'])) for index, n in data5.iterrows() 
                for nn in list(data6[np.logical_and(np.logical_or(data6.source==n.ref, data6.target==n.ref),
                   np.logical_or(data6.source==n.levels_ref, data6.target==n.levels_ref))].type)]
