public class SubmitCaseController {
    public Case c { get; set; }
    public SubmitCaseController() {
        c = new Case();
    }
    public PageReference submitCase() {
        try {            
            INSERT c;
            System.debug(c);
            return new PageReference('/' + c.Id);
        } catch (Exception e) {
            ApexPages.addMessages(e);
            return null;
        }
	}
}