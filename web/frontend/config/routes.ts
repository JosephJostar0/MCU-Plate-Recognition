export default [
  { path: '/user', layout: false, routes: [{ path: '/user/login', component: './User/Login' }] },
  { path: '/admin', layout: false, routes: [
      { path: '/admin/index', component: './TableList' },
    ] 
  },
  // { path: '/test', layout: true, routes: [{path:'/test', component:'./Test'}]},
  { path: '*', layout: false, component: './404' },
];
