import {
  ProColumns,
  ProFormInstance,
  ProTable,
  ProFormDateTimePicker,
  ProFormRadio,
  ProFormSelect,
  ProFormText,
  ProFormTextArea,
  StepsForm,
} from '@ant-design/pro-components';
import '@umijs/max';
import { Modal } from 'antd';
import React, { useEffect, useRef } from 'react';
export type UpdateFormProps = {
  values: API.RuleListItem;
  columns: ProColumns<API.RuleListItem>[];
  onCancel: ()=> void;
  onSubmit: (values: API.RuleListItem) => Promise<void>;
  visible:boolean;
};
const UpdateForm: React.FC<UpdateFormProps> = (props) => {
  const {values, visible, columns, onCancel, onSubmit} = props;
  const formRef = useRef<ProFormInstance>();
  useEffect(() => {
    if (formRef) {
      formRef.current?.setFieldsValue(values);
    }
  },[values])
  return (
    <Modal visible={visible} footer={null} onCancel={()=>onCancel?.()}>
    {
      <ProTable
        type="form"
        formRef={formRef}
        columns={columns}
        onSubmit={async (value) => {
          onSubmit?.(value);
        }}
      />
    }
    </Modal>
  );
};
export default UpdateForm;
