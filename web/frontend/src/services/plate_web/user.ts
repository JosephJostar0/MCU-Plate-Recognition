// @ts-ignore
/* eslint-disable */
import { request } from '@umijs/max';

/** login POST /user/login */
export async function userLoginUserLoginPost(
  body: API.LoginRequest,
  options?: { [key: string]: any },
) {
  return request<any>('/user/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/** logout POST /user/logout */
export async function userLogoutUserLogoutPost(options?: { [key: string]: any }) {
  return request<any>('/user/logout', {
    method: 'POST',
    ...(options || {}),
  });
}
