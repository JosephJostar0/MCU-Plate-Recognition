import { PlusOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns, ProDescriptionsItemProps } from '@ant-design/pro-components';
import {
  FooterToolbar,
  ModalForm,
  PageContainer,
  ProDescriptions,
  ProFormText,
  ProFormTextArea,
  ProTable,
} from '@ant-design/pro-components';
import '@umijs/max';
import { Button, Drawer, Input, List, Row, message } from 'antd';
import React, { useRef, useState } from 'react';
// import type { FormValueType } from './components/UpdateForm';
import UpdateForm from './components/UpdateForm';
import { addPlatePlateAddPost, alterPlatePlateAlterPost, deletePlatePlateDeletePost, listPlatePlateListPost, updatePlatePlateUpdatePost,currentPlatePlateCurrentPost } from '@/services/plate_web/plate';


const TableList: React.FC = () => {
  /**
   * @en-US Pop-up window of new window
   * @zh-CN 新建窗口的弹窗
   *  */
  const [createModalOpen, handleModalOpen] = useState<boolean>(false);
  /**
   * @en-US The pop-up window of the distribution update window
   * @zh-CN 分布更新窗口的弹窗
   * */
  const [updateModalOpen, handleUpdateModalOpen] = useState<boolean>(false);
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const actionRef = useRef<ActionType>();
  const [currentRow, setCurrentRow] = useState<API.RuleListItem>();
  const [selectedRowsState, setSelectedRows] = useState<API.RuleListItem[]>([]);


  /**
 * @en-US Add node
 * @zh-CN 添加节点
 * @param fields
 */
const handleAdd = async (fields: API.RuleListItem) => {
  const hide = message.loading('正在添加');
  try {
    const msg = await addPlatePlateAddPost({
      number: fields.number,
    });
    hide();
    if (msg.code !== 0){
      message.error(msg.status);
      return false;
    }
    message.success('Added successfully');
    return true;
  } catch (error) {
    hide();
    message.error('Adding failed, please try again!');
    return false;
  }
};

/**
 * @en-US Update node
 * @zh-CN 更新节点
 *
 * @param fields
 */
const handleUpdate = async (fields: API.RuleListItem) => {
  const hide = message.loading('Configuring');
  if (!currentRow) {
    message.warning("no current row!")
    return;
  }
  try {
    const res = await updatePlatePlateUpdatePost({
      pid: currentRow.pid,
      number: fields.number,
      access: currentRow.access,
    });
    hide();
    if (res.code === 1){
      message.error(res.status);
      return false;
    }
    message.success('Configuration is successful');
    return true;
  } catch (error) {
    hide();
    message.error('Configuration failed, please try again!');
    return false;
  }
};

/**
 *  Delete node
 * @zh-CN 删除节点
 *
 * @param selectedRow
 */
const handleRemove = async (selectedRow: API.RuleListItem) => {
  const hide = message.loading('正在删除');
  if (!selectedRow) return true;
  try {
    await deletePlatePlateDeletePost({
      pid: selectedRow.pid,
    });
    hide();
    message.success('Deleted successfully and will refresh soon');
    return true;
  } catch (error) {
    hide();
    message.error('Delete failed, please try again');
    return false;
  }
};

const handleAccess = async (selectedRow: API.RuleListItem) => {
  const hide = message.loading('changing access.');
  if (!selectedRow) return true;
  try {
    await alterPlatePlateAlterPost({
      pid: selectedRow.pid,
    });
    hide();
    message.success('Deleted successfully and will refresh soon');
    return true;
  } catch (error) {
    hide();
    message.error('Delete failed, please try again');
    return false;
  }

}


  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */

  const columns: ProColumns<API.RuleListItem>[] = [
    {
      title: 'id',
      dataIndex: 'pid',
      valueType: 'index',
    },
    {
      title: '车牌号',
      dataIndex: 'number',
      valueType: 'textarea',
    },
    {
      title: '权限',
      dataIndex: 'access',
      hideInForm: true,
      valueEnum: {
        0: {
          text: '拒绝',
          status: 'Default',
        },
        1: {
          text: '允许',
          status: 'Processing',
        }
      },
    },
    {
      title: '操作',
      dataIndex: 'option',
      valueType: 'option',
      render: (_, record) => [
        <a
          key="config"
          onClick={() => {
            handleUpdateModalOpen(true);
            setCurrentRow(record);
          }}
        >
          修改
        </a>,
        
        record.access === 0?
        <a
          key="del"
          onClick = {() => {
            handleAccess(record);
            actionRef.current?.reloadAndRest?.();
          }}
        >
          授权
        </a> :
        <a
          key="del"
          onClick = {() => {
            handleAccess(record);
            actionRef.current?.reloadAndRest?.();
          }}
        >
          禁止
        </a>       
        ,
        <Button
          key="del"
          danger
          type = "text"
          onClick = {() => {
            handleRemove(record);
            actionRef.current?.reloadAndRest?.();
          }}
        >
          删除
        </Button>,
      ],
    },
  ];
  
    const test =async () => {
      const msg = await currentPlatePlateCurrentPost();
      if (msg.code === 0){
        if (msg.data[0].access===1) {
          message.success(msg.data[0].plate);
        } else {
          message.warning(msg.data[0].plate);
        }
      }
    }
    const intervalId = setInterval(test, 5000);

  return (
    <PageContainer>
      <ProTable<API.RuleListItem, API.PageParams>
        headerTitle={'查询表格'}
        actionRef={actionRef}
        rowKey="key"
        search={{
          labelWidth: 120,
        }}
        toolBarRender={() => [
          <Button
            type="primary"
            key="primary"
            onClick={() => {
              handleModalOpen(true);
            }}
          >
            <PlusOutlined /> 新建
          </Button>,
        ]}
        request={async (params, sort: Record<string, SortOrder>, filter: Record<string, React.ReactText[] | null>) => {
                  const res = await listPlatePlateListPost({
                    ...params
                  })
                  if (res?.data) {
                    return  {
                      data: res?.data || [],
                      success: true,
                      total: res.total,
                    }
                  }
                }}
        columns={columns}
        rowSelection={{
          onChange: (_, selectedRows) => {
            setSelectedRows(selectedRows);
          },
        }}
      />
      {selectedRowsState?.length > 0 && (
        <FooterToolbar
          extra={
            <div>
              已选择{' '}
              <a
                style={{
                  fontWeight: 600,
                }}
              >
                {selectedRowsState.length}
              </a>{' '}
              项 &nbsp;&nbsp;
            </div>
          }
        >
          <Button
            onClick={async () => {
              await handleRemove(selectedRowsState);
              setSelectedRows([]);
              actionRef.current?.reloadAndRest?.();
            }}
          >
            批量删除
          </Button>
          {/* <Button type="primary">批量审批</Button> */}
        </FooterToolbar>
      )}


      <ModalForm
        title={'新增车牌'}
        width="400px"
        open={createModalOpen}
        onOpenChange={handleModalOpen}
        onFinish={async (value) => {
          const success = await handleAdd(value as API.RuleListItem);
          if (success) {
            handleModalOpen(false);
            if (actionRef.current) {
              actionRef.current.reload();
            }
          }
        }}
      >
        <ProFormText
          rules={[
            {
              required: true,
              message: '车牌号为必填项',
            },
          ]}
          width="md"
          name="number"
        />
      </ModalForm>
      

      <UpdateForm
        columns={columns}
        onSubmit={async (value) => {
          const success = await handleUpdate(value);
          if (success) {
            handleUpdateModalOpen(false);
            setCurrentRow(undefined);
            if (actionRef.current) {
              actionRef.current.reload();
            }
          }
        }}
        onCancel={() => {
          handleUpdateModalOpen(false);
          if (!showDetail) {
            setCurrentRow(undefined);
          }
        }}
        // updateModalOpen={updateModalOpen}
        values={currentRow || {}}
        visible={updateModalOpen}
      />

      <Drawer
        width={600}
        open={showDetail}
        onClose={() => {
          setCurrentRow(undefined);
          setShowDetail(false);
        }}
        closable={false}
      >
        {currentRow?.pid && (
          <ProDescriptions<API.RuleListItem>
            column={2}
            title={currentRow?.pid}
            request={async () => ({
              data: currentRow || {},
            })}
            params={{
              id: currentRow?.pid,
            }}
            columns={columns as ProDescriptionsItemProps<API.RuleListItem>[]}
          />
        )}
      </Drawer>

    </PageContainer>
  );
};
export default TableList;
