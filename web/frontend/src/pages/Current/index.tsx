import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { Card, theme, message} from 'antd';
import React, { useEffect, useState } from 'react';
import { currentPlatePlateCurrentPost } from '@/services/plate_web/plate';


const InfoCard: React.FC<{
  title: string;
  index: string;
  desc: string;
  valid: string;
  href: string;
}> = ({ title, href, index, desc, valid }) => {
  const { useToken } = theme;

  const { token } = useToken();

  return (
    <div
      style={{
        backgroundColor: token.colorBgContainer,
        boxShadow: token.boxShadow,
        borderRadius: '8px',
        fontSize: '14px',
        color: token.colorTextSecondary,
        lineHeight: '22px',
        padding: '16px 19px',
        minWidth: '220px',
        flex: 1,
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '4px',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            lineHeight: '22px',
            backgroundSize: '100%',
            textAlign: 'center',
            padding: '8px 16px 16px 12px',
            color: '#FFF',
            fontWeight: 'bold',
            backgroundImage:
              "url('https://gw.alipayobjects.com/zos/bmw-prod/daaf8d50-8e6d-4251-905d-676a24ddfa12.svg')",
          }}
        >
          {index}
        </div>
        <div
          style={{
            fontSize: '16px',
            color: token.colorText,
            paddingBottom: 8,
          }}
        >
          {title}
        </div>
      </div>
      <div
        style={{
          fontSize: '27px',
          color: token.colorTextSecondary,
          textAlign: 'justify',
          lineHeight: '32px',
          marginBottom: 8,
        }}
      >
        {desc}
      </div>
      <div
        style={{
          fontSize: '20px',
          color: token.colorTextSecondary,
          textAlign: 'justify',
          lineHeight: '25px',
          marginBottom: 10,
        }}
      >
        {valid}
      </div>
    </div>
  );
};

const Welcome: React.FC = () => {
  const { token } = theme.useToken();
  const { initialState } = useModel('@@initialState');

  // State for currentPlate
  const [currentPlate, setCurrentPlate] = useState<string>("no plate detected.");
  const [currentAccess, setCurrentAccess] = useState<string>("no access.");

  // Function to fetch data
  const fetchData = async () => {
    const msg = await currentPlatePlateCurrentPost();
    setCurrentPlate(msg.data[0].plate);
    setCurrentAccess(
      msg.data[0].access === 0 ?
      "Permission denied.":"Permission granted."
      )
  };

    // useEffect for calling fetchData every 10 seconds
  useEffect(() => {
    const intervalId = setInterval(fetchData, 8000);
    return () => clearInterval(intervalId); // Cleanup function to clear interval
  }, []); // Empty dependency array to run effect only once on component mount


  return (
    <PageContainer>
      <Card
        style={{
          borderRadius: 8,
        }}
        bodyStyle={{
          backgroundImage:
            initialState?.settings?.navTheme === 'realDark'
              ? 'background-image: linear-gradient(75deg, #1A1B1F 0%, #191C1F 100%)'
              : 'background-image: linear-gradient(75deg, #FBFDFF 0%, #F5F7FF 100%)',
        }}
      >
        <div
          style={{
            backgroundPosition: '100% -30%',
            backgroundRepeat: 'no-repeat',
            backgroundSize: '274px auto',
            backgroundImage:
              "url('https://gw.alipayobjects.com/mdn/rms_a9745b/afts/img/A*BuFmQqsB2iAAAAAAAAAAAAAAARQnAQ')",
          }}
        >
          <div
            style={{
              fontSize: '20px',
              color: token.colorTextHeading,
            }}
          >
            欢迎使用 MCU-Plate-Recognization based on YOLOv8
          </div>
          <p
            style={{
              fontSize: '14px',
              color: token.colorTextSecondary,
              lineHeight: '22px',
              marginTop: 16,
              marginBottom: 32,
              width: '65%',
            }}
          >
          YOLO（You Only Look Once）是一种快速的目标检测算法，通过将图像划分为网格单元，每个单元同时预测多个边界框和类别概率，实现在单次前向传递中完成目标检测的效果。
          </p>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
            }}
          >
            <InfoCard
              index="*"
              href="https://umijs.org/docs/introduce/introduce"
              title="当前检测到的车牌号:"
              desc= {currentPlate}
              valid= {currentAccess}
            />
          </div>
        </div>
      </Card>
    </PageContainer>
  );
};

export default Welcome;
