import request from '@/utils/request'

export function apiProductList() {
  return request({
    url: '/api/product/list',
    method: 'get'
  })
}

export function apiProductCreate(requestBody) {
  return request({
    url: '/api/product/create',
    method: 'post',
    data: requestBody
  })
}

export function apiProductUpdate(requestBody) {
  return request({
    url: '/api/product/update',
    method: 'post',
    data: requestBody
  })
}

export function apiProductDelete(id) {
  return request({
    url: '/api/product/delete',
    method: 'delete',
    params: {
      'id': id
    }
  })
}

// 软删除，更改数据状态
export function apiProductRemove(id) {
  return request({
    url: '/api/product/remove',
    method: 'post',
    params: {
      'id': id
    }
  })
}

