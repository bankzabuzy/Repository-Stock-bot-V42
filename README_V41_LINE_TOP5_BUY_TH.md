# V41 LINE Top 5 Buy Ranking

เพิ่มความสามารถให้ LINE Bot ตอบคำถาม Top 5 หุ้นที่น่าเข้าซื้อมากที่สุดของวัน

## คำสั่งใน LINE
- top5
- /top5
- top5 buy
- หุ้นน่าซื้อ
- หุ้นน่าเข้าซื้อ
- วันนี้ซื้ออะไร
- ตัวไหนน่าซื้อ
- จัดอันดับหุ้น

## Endpoint ใหม่
- /v41/top5-buy
- /api/top5-buy

## หลักการจัดอันดับ
ระบบจัดอันดับจาก AI Score, Probability, Confidence, Signal, Regime, Bias, RSI และ RVOL โดยเน้นตัวที่มีโอกาสทำกำไรและผ่านมุมมองเชิงบวกมากที่สุด ไม่ใช่เรียงตาม Score อย่างเดียว

หมายเหตุ: ใช้เพื่อ Paper Trading และ Decision Support ไม่ใช่คำสั่งซื้ออัตโนมัติ
