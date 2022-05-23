import uuid, shortuuid

def fhirBundlifyList(list, total, facade_url, page_store_time, page_size, uid="", lastPage=False):
    if(uid==""):
        uid = shortuuid.encode(uuid.uuid4())
    if(lastPage):
        linkList = [{"relation":"self","url":f"{facade_url}Page?_count={page_size}&__t={page_store_time}&__page-id={uid}"}]
        nextUuid = ""
    else:
        nextUuid = shortuuid.encode(uuid.uuid4())
        linkList = [{"relation":"self","url":f"{facade_url}Page?_count={page_size}&__t={page_store_time}&__page-id={uid}"},
                    {"relation":"next","url":f"{facade_url}Page?_count={page_size}&__t={page_store_time}&__page-id={nextUuid}"}]
    return {
        "id":uid, 
        "type":"searchset",
        "entry":list,
        "link":linkList,
        "total":total,
        "resourceType":"Bundle"
    }, nextUuid