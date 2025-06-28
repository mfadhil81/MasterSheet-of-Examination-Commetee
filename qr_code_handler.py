import uuid
import qrcode
import cv2
from pyzbar.pyzbar import decode

# دالة لإنشاء QR Code فريد لكل نسخة من البرنامج
def create_license_qr():
    unique_id = str(uuid.uuid4())  # معرف فريد لكل نسخة
    qr = qrcode.make(unique_id)
    qr.save("license_qr.png")
    print("تم إنشاء QR Code للترخيص بنجاح!")
    return unique_id

# دالة لفتح الكاميرا والتحقق من QR Code
def scan_qr_with_camera(license_id):
    cap = cv2.VideoCapture(0)
    print("قم بتوجيه QR Code أمام الكاميرا للتحقق من الترخيص...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("لم يتم العثور على كاميرا.")
            break

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            qr_data = obj.data.decode("utf-8")
            if qr_data == license_id:
                print("تم التحقق من الترخيص بنجاح!")
                cap.release()
                cv2.destroyAllWindows()
                return True

        cv2.imshow("QR Code Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("فشل التحقق من الترخيص.")
    return False

