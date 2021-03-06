import סטנפורד.קאראל.*;
public class מהמורותמילויקארל extends קארל {
   public void run() {
      מהלך_\_לזוז_\_לעבור();
      מילוי();
      מהלך_\_לזוז_\_לעבור();
   }

   /**
    * ממלא את המכל מתחת למיקום הנוכחי של קארל על ידי
    * הנחת ביפר בפינה. כדי ששיטה זו תעבוד כראוי, קארל
    * חייב להיות פונה מזרחה מעל למזרח. עם סיום הביצוע,
    * קארל יחזור לאותו ריבוע ויהיה שוב פונה מזרחה.
    */
   private void מילוי() {
      פנהימינה();
      מהלך_\_לזוז_\_לעבור();
      שיםאתביפר();
      תסתובב();
      מהלך_\_לזוז_\_לעבור();
      פנהימינה();
   } 

   /** הופך קארל 90 מעלות ימינה. */
   public void פנהימינה() {
      פונהשמאלה();
      פונהשמאלה();
      פונהשמאלה();
   }

   /** הופכת קארל סביב 180 מעלות. */
   public void תסתובב() {
      פונהשמאלה();
      פונהשמאלה();
   }
}