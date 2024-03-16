// @ts-ignore
/* eslint-disable */
import { request } from '@umijs/max';

/** add plate POST /plate/add */
export async function addPlatePlateAddPost(
  body: API.PlateAddRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/plate/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** alter access POST /plate/alter */
export async function alterPlatePlateAlterPost(
  body: API.PlateDeleteRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/plate/alter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** check plate POST /plate/check */
export async function checkPlatePlateCheckPost(
  body: API.PlateCheckRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/plate/check', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** delete plate POST /plate/delete */
export async function deletePlatePlateDeletePost(
  body: API.PlateDeleteRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/plate/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** list plate POST /plate/list */
export async function listPlatePlateListPost(options?: { [key: string]: any }) {
  return request<any>('/plate/list', {
    method: 'POST',
    ...(options || {}),
  });
}

/** update plate POST /plate/update */
export async function updatePlatePlateUpdatePost(
  body: API.PlateUpdateRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/plate/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}
