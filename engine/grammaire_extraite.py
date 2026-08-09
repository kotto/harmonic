# Règles de grammaire extraites automatiquement des 1101 problèmes GSM8K
# 721 motifs uniques (fenêtres autour des nombres)

REGLES_EXTRACTED = [
    # freq=5
    (r'<OBJ>\ <OBJ>\ each\ <OBJ>\ has\ <N>\ <OBJ>\ each', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=5
    (r'<OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ be\ sold\ \|\ be\ sold\ at\ \$1\.5\ each\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ cost\ \$2\ \|\ <OBJ>\ cost\ \$2\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ cost\ \$1\.25\ each', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=5
    (r'<OBJ>\ of\ <OBJ>\ cost\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=4
    (r'Neil\ has\ been\ saving\ 2/5\ times\ more\ coins\ in\ his\ piggy\ bank\ per\ month\ than\ Rong\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=4
    (r'total\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ of\ <OBJ>\ <ENT>\ <ENT>\ \|\ <OBJ>\ <ENT>\ <ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ of\ <ENT>\ <ENT>\ <ENT>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=4
    (r'<ENT>\ <OBJ>\ cost\ \$200\ <OBJ>\ <N>\ <OBJ>\ costs\ \$20\ each\ <OBJ>\ \|\ each\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ cost\ \$12\ each', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=4
    (r'<OBJ>\ has\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ at\ \|\ <OBJ>\ at\ \$4\ each\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ each\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'If\ the\ shipping\ company\ charges\ \$0\.35\ per\ pound\ plus\ \$0\.08\ per\ mile,\ and\ Amazon\ will\ only\ refund\ 75%\ of\ the\ book's\ purchase\ price,\ how\ much\ money\ will\ Milly\ lose\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'<OBJ>\ if\ <OBJ>\ have\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'while\ the\ second\ amusement\ park\ has\ a\ \$14\ fee\ for\ each\ adult\ and\ \$10\ for\ each\ child\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'<ENT>\ has\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'If\ drinks\ and\ snacks\ cost\ \$2\ each,\ how\ much\ money,\ in\ dollars,\ has\ the\ group\ spent\ overall\ on\ snacks\ and\ drinks\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'<ENT>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ a', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'On\ Tuesdays\ and\ Thursdays,\ he\ has\ two\ 2\-hour\ classes\ each\ day\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'If\ each\ bus\ trip\ costs\ her\ \$2\.20,\ how\ much\ would\ she\ save\ by\ buying\ a\ weekly\ bus\ pass\ for\ \$20\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'One\ glass\ costs\ \$5,\ but\ every\ second\ glass\ costs\ only\ 60%\ of\ the\ price\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ half\ as\ \|\ 5th\ <OBJ>\ <OBJ>\ have\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'If\ Zaid\ earns\ 6000\$\ per\ month,\ how\ much\ money\ will\ he\ still\ have\ after\ all\ these\ expenses\ and\ donations\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=3
    (r'if\ <OBJ>\ buy\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'What's\ the\ total\ amount\ of\ money\ he\ will\ spend\ if\ each\ pepper\ costs\ 15\$\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'Suppose\ Karen\ chooses\ to\ do\ both\ and\ would\ also\ like\ to\ add\ nail\ art\ on\ each\ of\ her\ fingers,\ which\ costs\ \$3\ per\ nail\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'has\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ every\ \|\ every\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'He\ has\ a\ collection\ of\ cards\ and\ plans\ to\ sell\ them\ for\ \$1\.5\ each\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ has\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'The\ first\ amusement\ park\ has\ a\ \$26\ fee\ for\ each\ adult\ and\ a\ \$12\ fee\ for\ each\ child;', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'he\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ he\ sells', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'he\ <OBJ>\ up\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$20\ each', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <ENT>\ has\ to\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'It\ costs\ \$25\ per\ session\ to\ rent\ the\ studio\ plus\ \$1\.50\ per\ student\ per\ session\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ each\ have\ <N>\ fewer\ <OBJ>\ than\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ on\ each\ of\ \|\ <OBJ>\ on\ each\ of\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ in\ it', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ have\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ in\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ of\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'Nathan\ has\ a\ bouncy\ ball\ that\ bounces\ to\ 2/3rds\ of\ its\ starting\ height\ with\ each\ bounce\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'The\ new\ carpet\ he's\ chosen\ costs\ \$12\ per\ square foot,\ plus\ \$2\ per\ square\ foot\ for\ padding\ underneath\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ has\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ \|\ of\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'if\ each\ <OBJ>\ <OBJ>\ costs\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ each\ \|\ <OBJ>\ each\ <OBJ>\ <OBJ>\ costs\ <N>\ <OBJ>\ <OBJ>\ much\ <OBJ>\ he', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'he\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ at\ \$0\.50', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ work\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ he\ has', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ at\ each\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ total\ <OBJ>\ \|\ of\ <OBJ>\ <OBJ>\ <OBJ>\ if\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ total\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'if\ each\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'On\ Mondays,\ Wednesdays,\ and\ Fridays,\ college\ student\ Kimo\ has\ three\ 1\-hour\ \ classes\ each\ day\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'he\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ each\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ is\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ by\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'The\ company\ has\ a\ policy\ of\ increasing\ the\ salaries\ of\ each\ of\ its\ employees\ by\ 10%\ of\ the\ initial\ salary\ every\ year\ for\ those\ who've\ stayed\ in\ the\ company\ for\ five\ years\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'if\ he\ has\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ has\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'an\ <OBJ>\ of\ m\&m\ has\ <N>\ m\&m\ in\ it\ <OBJ>\ many\ \|\ he\ make\ if\ he\ <OBJ>\ <N>\ in\ each\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'Peter\ has\ \$70\ and\ wishes\ to\ spend\ an\ equal\ amount\ each\ day\ for\ one\ week\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ mb\ has\ <N>\ kb\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ mb\ has\ <N>\ kb\ <OBJ>\ <OBJ>\ to\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'costs\ \$0\.40\ <OBJ>\ much\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ cost\ \|\ much\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ cost\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'zoey's\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ each\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'sydney's\ has\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ has\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ in\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ in\ each\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'To\ make\ a\ profit\ of\ \$2000,\ Isaias\ has\ to\ sell\ the\ chickens\ he\ planned\ to\ take\ to\ the\ market\ from\ his\ farm\ at\ \$50\ per\ chicken\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ <ENT>\ have\ <OBJ>\ of\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ have\ <OBJ>\ of\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ many', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'if\ <ENT>\ makes\ <N>\ s'mores\ <OBJ>\ makes\ <N>\ s'mores\ \|\ makes\ <N>\ s'mores\ <OBJ>\ makes\ <N>\ s'mores\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ s'mores\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'If\ it\ costs\ \$2\ to\ transport\ each\ bag\ from\ the\ farm\ to\ the\ warehouse,\ and\ the\ trader\ made\ a\ total\ profit\ of\ \$400\ after\ selling\ all\ the\ bags\ at\ a\ rate\ of\ \$30\ each,\ how\ many\ bags\ did\ he\ sell\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ costs\ \$12\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ costs\ \|\ <OBJ>\ <OBJ>\ costs\ \$3\ each\ <N>\ <OBJ>\ <OBJ>\ cost\ \$1\.50\ each', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'How\ many\ boxes\ of\ pizza\ did\ Marie\ order\ if\ each\ box\ costs\ \$8\.50\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'If\ she\ continues\ to\ save\ the\ same\ amount\ each\ week,\ how\ many\ more\ weeks\ will\ it\ take\ for\ her\ to\ have\ saved\ a\ total\ of\ \$60\?', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=2
    (r'Each\ class\ has\ the\ same\ amount\ of\ students,\ and\ in\ each\ class\ 40%\ of\ the\ students\ are\ girls\.', 'CROSS_MULT', ['container', 'per_unit', 'product']),
    # freq=5
    (r'<ENT>\ has\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=4
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=3
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'in\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ 20%\ <OBJ>\ in\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'Aleena\ subscribed\ to\ a\ streaming\ service\ that\ charges\ her\ \$140\ per\ month\.', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'if\ he\ buys\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ much', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ \|\ <ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'he\ <OBJ>\ <OBJ>\ <N>\ feet/hour\ <OBJ>\ <OBJ>\ <OBJ>\ half', 'DIV', ['val']),
    # freq=2
    (r'At\ a\ spa,\ Iris\ spent\ \$400\ to\ do\ her\ hair,\ 1/4\ as\ much\ to\ do\ a\ manicure,\ and\ 3/4\ as\ much\ money\ as\ a\ manicure\ to\ do\ a\ pedicure\.', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <ENT>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ in\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>\ or\ <N>\ <OBJ>\ in\ \|\ <OBJ>\ in\ <N>\ <OBJ>\ or\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'albert's\ <OBJ>\ is\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ has\ a\ <OBJ>\ of\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'is\ <OBJ>\ to\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ each\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'One\ has\ 1/6\ left,\ the\ second\ has\ 2/3\ left\ and\ the\ third\ one\ has\ 1/2\ left\.', 'DIV', ['val']),
    # freq=2
    (r'if\ each\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ in\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'if\ kate’s\ <N>\ <OBJ>\ each\ eat\ <N>\ <OBJ>\ \|\ kate’s\ <N>\ <OBJ>\ each\ eat\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ many', 'DIV', ['val']),
    # freq=2
    (r'it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'In\ a\ grocery\ store,\ four\ apples\ cost\ \$5\.20,\ and\ three\ oranges\ cost\ \$3\.30\.', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'DIV', ['val']),
    # freq=2
    (r'an\ <OBJ>\ <OBJ>\ <OBJ>\ makes\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ of\ <OBJ>\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'If\ Aries\ is\ sure\ to\ get\ 75%\ of\ the\ easy\ questions,\ and\ half\ of\ the\ average\ and\ difficult\ questions\ correctly,\ how\ many\ points\ is\ she\ sure\ to\ get\?', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ make\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ make\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ a\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ each\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ to\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ half', 'DIV', ['val']),
    # freq=2
    (r'it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ each\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ he\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ every\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <ENT>\ had\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ each\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ spends\ <N>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <OBJ>\ \|\ an\ <OBJ>\ <OBJ>\ <ENT>\ spends\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ has\ <N>\ more\ <OBJ>\ than\ <ENT>', 'DIV', ['val']),
    # freq=2
    (r'James\ loves\ to\ go\ swimming\ and\ has\ to\ swim\ across\ a\ 20\-mile\ lake\.', 'DIV', ['val']),
    # freq=2
    (r'They\ each\ had\ \$60\.', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ had\ <N>\ <OBJ>\ 2/5\ of\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ was\ <N>\ more\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ was\ <N>\ more\ than\ <OBJ>\ <ENT>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'Poppy\ is\ solving\ a\ 1000\-piece\ jigsaw\ puzzle\.', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ many\ more', 'DIV', ['val']),
    # freq=2
    (r'to\ sell\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ have\ a\ total\ of\ <N>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'He\ gives\ his\ daughter\ 200\$\ to\ use\ for\ her\ weekly\ expenses\ and\ 700\$\ to\ his\ wife\ to\ budget\ for\ groceries\ and\ other\ household\ goods\.', 'DIV', ['val']),
    # freq=2
    (r'How\ much\ more\ does\ it\ cost\ for\ a\ mixture\ of\ 1/2\ pound\ almonds\ and\ 1/3\ pound\ walnuts\ than\ a\ mixture\ of\ 1/5\ pound\ almonds\ and\ 1/3\ pound\ walnuts\?', 'DIV', ['val']),
    # freq=2
    (r'he\ <OBJ>\ buy\ <N>\ <OBJ>\ <OBJ>\ \$500', 'DIV', ['val']),
    # freq=2
    (r'if\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ in\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ is\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'DIV', ['val']),
    # freq=5
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=5
    (r'<OBJ>\ <OBJ>\ if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=5
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=5
    (r'<OBJ>\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ more\ <ENT>\ <ENT>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=5
    (r'<N>\ <OBJ>\ <OBJ>\ <OBJ>\ extra\-small', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'She\ spent\ \$12\ on\ ingredients\ for\ the\ cake,\ \$43\ on\ birthday\ presents,\ \$15\ on\ decorations,\ \$4\ on\ invitations,\ and\ \$22\ on\ goodie\ bags\ for\ the\ party\ guests\.', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ third\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'on\ <ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ had\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ \|\ had\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ than\ <OBJ>\ had', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'<ENT>\ <ENT>\ <OBJ>\ <N>\ fewer\ <OBJ>\ than\ <ENT>\ <N>\ \|\ <N>\ fewer\ <OBJ>\ than\ <ENT>\ <N>\ fewer\ <OBJ>\ <OBJ>\ than\ <ENT>\ \|\ <OBJ>\ <OBJ>\ than\ <ENT>\ <OBJ>\ <N>\ more\ <OBJ>\ than\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'Carmen\ has\ \$100,\ Samantha\ has\ \$25\ more\ than\ Carmen,\ and\ Daisy\ has\ \$50\ more\ than\ Samantha\.', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'he\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ he\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ on\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <ENT>\ <OBJ>\ <N>\ on\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ on\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ an\ <N>\ on\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ an\ <N>\ on\ <OBJ>\ 4th\ <OBJ>\ was\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'The\ king\ cab\ is\ an\ extra\ \$7,500,\ leather\ seats\ are\ one\-third\ the\ cost\ of\ the\ king\ cab\ upgrade,\ running\ boards\ are\ \$500\ less\ than\ the\ leather\ seats,\ and\ the\ upgraded\ exterior\ light\ package\ is\ \$1500\.', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ be\ \|\ <OBJ>\ <OBJ>\ to\ be\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ be', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'dj\ has\ <N>\ <OBJ>\ <ENT>\ has\ <N>\ <OBJ>\ \|\ has\ <N>\ <OBJ>\ <ENT>\ has\ <N>\ <OBJ>\ rj\ has\ <N>\ <OBJ>\ \|\ has\ <N>\ <OBJ>\ rj\ has\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ has\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ has\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'The\ bagel\ cost\ \$4,\ and\ the\ soup\ 25%\ more\.', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'She\ makes\ enough\ to\ fill\ a\ 10\-ounce\ jar\ each\ time\.', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ gave\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ total\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ to\ <OBJ>\ \|\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <ENT>\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ what's\ <OBJ>\ total', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'company's\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ each\ <OBJ>\ is\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'of\ <OBJ>\ are\ there\ in\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <N>\ <OBJ>\ <OBJ>\ on\ <ENT>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ if\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ he', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'a\ 30\-minute\ <OBJ>\ \$4/pill\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$6/hour\ <OBJ>\ a\ \|\ <OBJ>\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ has\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ is\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'he\ buys\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ he\ buys\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'She\ had\ a\ coupon\ for\ \$2\ off\ the\ package\ of\ \$8\ athletic\ socks\ that\ she\ also\ bought\.', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=3
    (r'If\ she\ wants\ to\ buy\ enough\ stuffed\ goats,\ such\ that\ the\ percentage\ of\ stuffed\ goats\ is\ 30%\ of\ all\ of\ her\ stuffed\ animals,\ how\ many\ stuffed\ goats\ should\ she\ buy\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'How\ much\ does\ replacing\ the\ movies\ cost\ if\ a\ normal\ movie\ costs\ \$10\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'He\ then\ sold\ the\ remaining\ land\ for\ \$3\ per\ square\ meter\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Half\ of\ them\ were\ Trekking\ bikes,\ and\ 15%\ were\ BMX\ bikes\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ to\ <OBJ>\ <N>\ times\ more\ <OBJ>\ than\ <ENT>\ \|\ <OBJ>\ than\ <ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ less\ than\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ installed/hung', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'on\ <ENT>\ he\ sold\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ fewer\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ ate\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'was\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ to\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'by\ <OBJ>\ b\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ \|\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ have\ <N>\ times\ <OBJ>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ was\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<N>\ more\ <OBJ>\ <OBJ>\ in\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'She\ trades\ 50%\ of\ her\ large\ stickers\ for\ large\ buttons\ and\ trades\ the\ rest\ of\ them\ for\ small\ buttons\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'After\ she\ returned\ the\ item,\ she\ bought\ a\ frying\ pan\ that\ was\ on\ sale\ for\ 20%\ off\ \$20\.00\ and\ a\ set\ of\ towels\ that\ was\ 10%\ off\ \$30\.00\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'of\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ more\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ much\ do\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ cost', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'\$125\ <OBJ>\ a\ <OBJ>\ of\ <N>\ <OBJ>\ \$6\ <OBJ>\ each\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ sister's\ <OBJ>\ has\ <N>\ more\ <OBJ>\ than\ half\ of', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ to\ <OBJ>\ <N>\ large\-sized\ <OBJ>\ <OBJ>\ <N>\ medium\-sized\ \|\ <OBJ>\ <N>\ large\-sized\ <OBJ>\ <OBJ>\ <N>\ medium\-sized\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ medium\-sized\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ small\-sized\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <N>\ times\ more\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Anis\ rowed\ 1/5\ times\ more\ miles\ than\ Dijana\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ has\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <OBJ>\ <N>\ more', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'At\ a\ spa,\ Iris\ spent\ \$400\ to\ do\ her\ hair,\ 1/4\ as\ much\ to\ do\ a\ manicure,\ and\ 3/4\ as\ much\ money\ as\ a\ manicure\ to\ do\ a\ pedicure\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ had\ <N>\ <OBJ>\ of\ <OBJ>\ <ENT>\ had\ \|\ <OBJ>\ of\ <OBJ>\ <ENT>\ had\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <ENT>\ \|\ of\ <OBJ>\ <OBJ>\ <ENT>\ had\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ duncan's\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ \|\ <OBJ>\ <OBJ>\ <ENT>\ be\ in\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ half\ as\ many\ \|\ as\ many\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'If\ Adrien's\ and\ Lylah's\ salary\ increased\ simultaneously,\ and\ Adrien\ earned\ \$40000\ four\ years\ ago,\ calculate\ the\ total\ salary\ the\ two\ were\ receiving\ four\ years\ later\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ had\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ than\ <OBJ>\ <OBJ>\ \|\ than\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Her\ student\ loans\ have\ a\ minimum\ payment\ of\ \$300/month,\ her\ credit\ card's\ minimum\ is\ \$200/month,\ and\ her\ mortgage's\ minimum\ is\ \$500/month\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'At\ check\ out,\ Marcus\ shows\ his\ loyalty\ card\ that\ gives\ him\ 10%\ off\ of\ his\ purchase\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'it\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ to\ make\ \|\ <OBJ>\ to\ make\ a\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ of\ <OBJ>\ \|\ a\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ times', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ has\ a\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ has\ a\ <OBJ>\ of\ <N>\ <OBJ>\ more\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Tim\ gets\ a\ promotion\ that\ offers\ him\ a\ 5%\ raise\ on\ his\ \$20000\ a\ month\ salary\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'albert's\ <OBJ>\ is\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ in\ it', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'He\ spent\ \$200\ on\ blue\ ties\ that\ cost\ \$40\ each\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ 2/5', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ he\ has\ to', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ an\ <OBJ>\ of\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Lani\ bought\ a\ pair\ of\ sunglasses\ at\ \$30\ and\ two\ bathrobes\ at\ \$100\ each\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ are\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ up\ <OBJ>\ <N>\ more\ <OBJ>\ there', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ total\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ spends\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ to\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ a\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'it\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ to\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ buys\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$4\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$4\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$2\ \|\ <OBJ>\ \$2\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$3', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$60\ in', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ bought\ <N>\ dozen\ <OBJ>\ <OBJ>\ cost\ \$68\ \|\ <OBJ>\ cost\ \$68\ per\ dozen\ <N>\ dozen\ <OBJ>\ <OBJ>\ <OBJ>\ cost\ \|\ cost\ \$80\ per\ dozen\ <OBJ>\ <N>\ dozen\ <OBJ>\ <OBJ>\ <OBJ>\ \$55', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'to\ <OBJ>\ <OBJ>\ <OBJ>\ bought\ <N>\ times\ <OBJ>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ much', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'on\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ more\ than\ one\-fifth\ as\ many', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ had\ <N>\ times\ more\ <OBJ>\ than\ <OBJ>\ \|\ times\ more\ <OBJ>\ than\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'he\ bought\ <N>\ <OBJ>\ <OBJ>\ cost\ \$1\.5\ each\ \|\ <OBJ>\ <OBJ>\ cost\ \$1\.5\ each\ <N>\ <OBJ>\ <OBJ>\ cost\ \$4\ each', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ sells\ <N>\ <OBJ>\ <OBJ>\ \$5\.50\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ \$11\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$1\.50\ each', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ has\ had\ <N>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ bought\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$2\.50\ \|\ <OBJ>\ <OBJ>\ \$2\.50\ each\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ at\ \$2\.00', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ bought\ <N>\ <OBJ>\ at\ \$0\.50\ each\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'have\ <OBJ>\ if\ <ENT>\ has\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ is\ <N>\ <OBJ>\ per\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ sells\ <N>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ \|\ sells\ <N>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ much', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ has\ <N>\ dozen\ <OBJ>\ <OBJ>\ a\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ a\ 10\-year\-old\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>\ of', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ ate\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ each\ an\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Red\ balls\ cost\ \$9,\ Blue\ balls\ cost\ \$5\ and\ green\ balls\ cost\ \$3\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ many', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ a\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'a\ quarter\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'He\ also\ has\ a\ collection\ of\ gerbils\ that's\ 1/3\ the\ number\ of\ fish\ he\ has\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <ENT>\ have\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ an\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <OBJ>\ \|\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'If\ a\ kilogram\ of\ tuna\ costs\ \$0\.50,\ how\ much\ will\ he\ earn\ after\ selling\ all\ the\ tunas\ to\ the\ market\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ buy\ <N>\ <OBJ>\ <OBJ>\ \$3\ each', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'had\ <OBJ>\ up\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ is\ <OBJ>\ total', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ <OBJ>\ every\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ are\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ gb/minute\ <OBJ>\ 40%\ of\ <OBJ>\ \|\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ spends\ <N>\ <OBJ>\ <OBJ>\ a\ <OBJ>\ half\ \|\ much\ <OBJ>\ <OBJ>\ it\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ it', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'The\ dress\ shirts\ were\ \$60\ each\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ a\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ each\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ half\ \|\ <OBJ>\ half\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'1/4\ of\ the\ seniors\ are\ officers\ and\ they\ will\ need\ to\ receive\ cords\ that\ are\ \$12\ each\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Nani's\ sister\ is\ 25%\ younger\ than\ him\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Tickets\ for\ Fridays\ and\ Saturdays\ cost\ \$10\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ is\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'on\ <ENT>\ <OBJ>\ <OBJ>\ sold\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ an\ \|\ to\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ more\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'He\ swims\ 60%\ of\ the\ distance\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'If\ Kelly’s\ budget\ is\ \$65\ then\ how\ much\ money,\ in\ dollars,\ does\ she\ have\ left\ in\ her\ budget\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Marie\ paid\ a\ total\ of\ \$50\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ was\ <N>\ more\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ was\ <N>\ more\ than\ <OBJ>\ <ENT>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'One\ notebook\ is\ sold\ at\ \$1\.50\ each,\ a\ pen\ at\ \$0\.25\ each,\ a\ calculator\ at\ \$12\ each,\ and\ a\ geometry\ set\ at\ \$10\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ is\ <N>\ less\ than\ <OBJ>\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ as\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ less\ than\ a\ <OBJ>\ \|\ than\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ more\ than\ a\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ he\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ buys\ <N>\ <OBJ>\ <OBJ>\ what's\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'on\ <ENT>\ he\ works\ <N>\ <OBJ>\ less\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ bought\ <N>\ more\ <OBJ>\ at\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ at\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ fewer\ <OBJ>\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'if\ bo\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ total\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ in\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ in\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'If\ she\ gave\ \$20,\ how\ much\ change\ did\ she\ receive\?', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ he\ sold\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'He\ decides\ to\ upgrade\ his\ meal\ for\ an\ extra\ \$3\.00\ which\ will\ add\ chips\ and\ a\ drink\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'Brittany's\ quilted\ comforter\ has\ many\ 1\-foot\ by\ 1\-foot\ colored\ squares\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ had\ <N>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ \|\ <OBJ>\ had\ <N>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ than\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <OBJ>\ \|\ <OBJ>\ than\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ fewer\ <OBJ>\ <OBJ>\ than\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'he\ bought\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ more\ \|\ bought\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'She\ has\ saved\ \$2\ from\ her\ allowance,\ and\ her\ mother\ gave\ her\ \$16\.', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ has\ <N>\ more\ than\ half\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ an\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ ate\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ ate\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ ate\ <N>\ more\ than\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ ate\ <N>\ more\ than\ <OBJ>\ <OBJ>', 'GAIN', ['ent', 'val']),
    # freq=4
    (r'He\ gave\ 1/2\ of\ his\ pencils\ to\ Brandon,\ and\ he\ gave\ 3/5\ of\ the\ remaining\ pencils\ to\ Charlie\.', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ gave\ \|\ <OBJ>\ <OBJ>\ gave\ <OBJ>\ remaining\ <N>\ <OBJ>\ to\ <ENT>', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=2
    (r'gave\ <OBJ>\ <OBJ>\ to\ <OBJ>\ <N>\ <OBJ>\ equally', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=2
    (r'His\ sister\ Ava\ gave\ him\ half\ of\ her\ \$90\ allowance\ to\ help\ him\ buy\ a\ new\ camera\ that\ costs\ \$200\.', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=2
    (r'While\ working\ at\ the\ restaurant,\ each\ of\ the\ forty\ customers\ who\ came\ into\ the\ restaurant\ gave\ Rafaela\ a\ \$20\ tip\.', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=2
    (r'Gabriel\ has\ \$5000\ from\ working\ on\ weekends\ and\ his\ brother\ gave\ him\ \$200\ to\ help\ him\.', 'GAVE_TO', ['giver', 'ent', 'val', 'obj']),
    # freq=5
    (r'<ENT>\ has\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=4
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=3
    (r'<ENT>\ had\ <N>\ <OBJ>\ 2/5\ of\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=3
    (r'on\ <OBJ>\ <OBJ>\ <OBJ>\ was\ <N>', 'LOSE', ['ent', 'val']),
    # freq=3
    (r'He\ wishes\ to\ save\ \$2000\ for\ this\ trip,\ how\ much\ does\ he\ have\ to\ spend\ on\ buying\ gifts\ for\ his\ business\ partners\ in\ South\ Africa\?', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ a\ horse\-drawn\ <OBJ>\ <OBJ>\ <N>\ pm\ to\ <N>\ pm\ \|\ <OBJ>\ <OBJ>\ <N>\ pm\ to\ <N>\ pm', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ earns\ \$5\ every\ <N>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ eats\ <N>\ on\ \|\ has\ <N>\ <OBJ>\ <OBJ>\ eats\ <N>\ on\ <OBJ>\ <OBJ>\ to\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'he\ eats\ <N>\ more\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ more\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ more\ in\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ bought\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <ENT>\ bought\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ a\ \|\ <OBJ>\ each\ <OBJ>\ <OBJ>\ a\ <N>\ percent\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ had\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ \|\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ up', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'in\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ 20%\ <OBJ>\ in\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ in\ a', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ \$15\ an\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ is', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'Job\ B\ pays\ \$42,000\ a\ year\ and\ is\ in\ a\ state\ that\ charges\ \$6,000\ in\ property\ tax\ and\ a\ 10%\ tax\ rate\ on\ net\ income\ after\ property\ tax\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'Roses\ cost\ \$2\ each\ and\ \$15\ for\ a\ dozen\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ he\ spends\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ in\ <OBJ>\ <OBJ>\ <OBJ>\ many\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ he\ buy\ \|\ he\ buy\ <OBJ>\ he\ buys\ <N>\ <OBJ>\ <OBJ>\ cost\ <N>\ <OBJ>\ \|\ buys\ <N>\ <OBJ>\ <OBJ>\ cost\ <N>\ <OBJ>\ each', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'of\ <OBJ>\ <OBJ>\ <OBJ>\ bought\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ were\ \$8\ a\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ \|\ <ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ as\ <OBJ>\ as\ <N>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ ate\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ was\ \|\ was\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ were\ <OBJ>\ so\ he', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ is\ <N>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'an\ <OBJ>\ every\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ every\ <OBJ>\ <OBJ>\ a', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ he\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ he\ has', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<N>\ <OBJ>\ to\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ to\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ on\ <N>\ more\ <OBJ>\ than\ <ENT>\ <OBJ>\ \|\ <OBJ>\ than\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ a\ total\ of\ <N>\ <OBJ>\ were\ <OBJ>\ <OBJ>\ of', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ eats\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ are', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'After\ each\ of\ them\ had\ given\ an\ equal\ amount\ of\ money\ to\ their\ little\ sister,\ Rissa\ is\ left\ with\ 4/5\ of\ her\ money\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'He\ paid\ \$400\ less\ for\ the\ printer\ than\ the\ computer\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ more\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'to\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ have\ <OBJ>\ is\ <N>\ <OBJ>\ many\ more\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'They\ each\ had\ \$60\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ to', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'Poppy\ is\ solving\ a\ 1000\-piece\ jigsaw\ puzzle\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ many\ more', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'She\ spent\ half\ of\ it\ on\ food\ and\ snacks,\ and\ an\ additional\ \$10\ for\ rides\.', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ have\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ have', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ ate\ <N>\ less\ than\ <N>\ <OBJ>\ of\ \|\ <ENT>\ ate\ <N>\ less\ than\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'he\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ at\ <OBJ>\ <OBJ>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'LOSE', ['ent', 'val']),
    # freq=7
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=6
    (r'<ENT>\ has\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=5
    (r'<OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=4
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ at\ \$3\.00\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ at\ \$3\.00\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ at\ \$2\.50\ each\ \|\ <OBJ>\ <OBJ>\ at\ \$2\.50\ each\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$4\.00\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ \$4\.00\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ were\ \$1\.00', 'MULT', ['val']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ are\ <N>\ x\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ are\ <N>\ x\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=4
    (r'<ENT>\ is\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=4
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=4
    (r'on\ <ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'MULT', ['val']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'The\ price\ of\ one\ MTB\ is\ \$500,\ BMX\ is\ half\ the\ price\ of\ an\ MTB,\ and\ a\ Trekking\ bike\ is\ \$450\.', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <ENT>\ has\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'to\ <OBJ>\ <OBJ>\ to\ buy\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ <OBJ>\ to\ buy\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ had\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'Tim\ gets\ a\ promotion\ that\ offers\ him\ a\ 5%\ raise\ on\ his\ \$20000\ a\ month\ salary\.', 'MULT', ['val']),
    # freq=3
    (r'She\ correctly\ answers\ 80%\ of\ the\ multiple\-choice\ questions,\ 90%\ of\ the\ true/false\ questions,\ and\ 60%\ of\ the\ long\-answer\ questions\.', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ 4\-minute\ <OBJ>\ <OBJ>\ each\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'of\ <OBJ>\ are\ there\ in\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<OBJ>\ buys\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$4\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$4\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$2\ \|\ <OBJ>\ \$2\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ \$3', 'MULT', ['val']),
    # freq=3
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'<OBJ>\ bought\ <N>\ dozen\ <OBJ>\ <OBJ>\ cost\ \$68\ \|\ <OBJ>\ cost\ \$68\ per\ dozen\ <N>\ dozen\ <OBJ>\ <OBJ>\ <OBJ>\ cost\ \|\ cost\ \$80\ per\ dozen\ <OBJ>\ <N>\ dozen\ <OBJ>\ <OBJ>\ <OBJ>\ \$55', 'MULT', ['val']),
    # freq=3
    (r'he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ each\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'of\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'if\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ if\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ he', 'MULT', ['val']),
    # freq=3
    (r'<ENT>\ sells\ <N>\ <OBJ>\ <OBJ>\ \$5\.50\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ \$11\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$1\.50\ each', 'MULT', ['val']),
    # freq=3
    (r'a\ <OBJ>\ <OBJ>\ has\ <N>\ dozen\ <OBJ>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'a\ 30\-minute\ <OBJ>\ \$4/pill\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$6/hour\ <OBJ>\ a\ \|\ <OBJ>\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ of\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'If\ one\ bag\ contains\ 50\-pounds\ of\ oats,\ \ how\ many\ bags\ of\ oats\ does\ he\ need\ to\ fed\ his\ horses\ for\ five\ days\?', 'MULT', ['val']),
    # freq=3
    (r'a\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ on\ a\ <OBJ>\ \|\ a\ <OBJ>\ every\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'Lauren\ is\ saving\ 20%\ of\ every\ paycheck\.', 'MULT', ['val']),
    # freq=3
    (r'<OBJ>\ a\ total\ <OBJ>\ of\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <ENT>\ \|\ <OBJ>\ <ENT>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>', 'MULT', ['val']),
    # freq=3
    (r'She\ bought\ three\ apples\ at\ \$1\.50\ each,\ five\ oranges\ at\ \$0\.80\ each,\ and\ six\ peaches\ at\ \$0\.75\ each\.', 'MULT', ['val']),
    # freq=2
    (r'he\ has\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'40%\ of\ the\ remaining\ movies\ are\ older\ movies\ which\ are\ \$5\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ sold\ <N>\ <OBJ>\ <OBJ>\ cost\ \$25,000\ each', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ up\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>\ every\ \|\ every\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ 50%\ more\ <OBJ>\ per', 'MULT', ['val']),
    # freq=2
    (r'He\ gets\ paid\ \$4\ per\ car\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ cost\ \$32\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ to\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Half\ of\ them\ were\ Trekking\ bikes,\ and\ 15%\ were\ BMX\ bikes\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ bought\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <ENT>\ bought\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ a', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ of\ <OBJ>\ had\ <N>\ <OBJ>\ in\ it', 'MULT', ['val']),
    # freq=2
    (r'it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ he', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ was\ <N>\ times\ <OBJ>\ <OBJ>\ of\ <ENT>', 'MULT', ['val']),
    # freq=2
    (r'in\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ 20%\ <OBJ>\ in\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Suddenly,\ a\ gust\ of\ wind\ caused\ 40%\ of\ the\ red\ balloons\ to\ burst\.', 'MULT', ['val']),
    # freq=2
    (r'total\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ eats\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <ENT>\ \|\ a\ <OBJ>\ <OBJ>\ <ENT>\ eats\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ \$15\ an\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ is', 'MULT', ['val']),
    # freq=2
    (r'Job\ B\ pays\ \$42,000\ a\ year\ and\ is\ in\ a\ state\ that\ charges\ \$6,000\ in\ property\ tax\ and\ a\ 10%\ tax\ rate\ on\ net\ income\ after\ property\ tax\.', 'MULT', ['val']),
    # freq=2
    (r'if\ <OBJ>\ bought\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ the\ streaming\ company\ charged\ her\ the\ initial\ amount\ for\ the\ first\ half\ of\ the\ year\ and\ then\ charged\ her\ 10%\ less\ money\ on\ the\ other\ half\ of\ the\ year,\ calculate\ the\ total\ amount\ she\ had\ paid\ for\ the\ streaming\ service\ by\ the\ end\ of\ the\ year\.', 'MULT', ['val']),
    # freq=2
    (r'In\ June,\ 1/4\ of\ the\ employees'\ contracts\ expired\.', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ \$20000\ in\ <N>', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ an\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ an\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ are\ \|\ <OBJ>\ a\ <OBJ>\ <OBJ>\ are\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'a\ 900\-watt\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'The\ rest\ of\ the\ people\ think\ horse\ \#12\ will\ win\ the\ big\ race\.', 'MULT', ['val']),
    # freq=2
    (r'Sheila\ charged\ \$85\.00\ worth\ of\ merchandise\ on\ her\ credit\ card\.', 'MULT', ['val']),
    # freq=2
    (r'She\ ended\ up\ returning\ one\ item\ that\ cost\ \$15\.00\.', 'MULT', ['val']),
    # freq=2
    (r'Each\ box\ is\ \$100\.00\ and\ currently\ 10%\ off\.', 'MULT', ['val']),
    # freq=2
    (r'he\ is\ <OBJ>\ <N>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ \|\ <ENT>\ of\ <OBJ>\ <N>\ <ENT>\ <N>\ <OBJ>\ 2/5\ are\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ he\ was\ stapling\ reports\ from\ 8:00\ AM\ until\ 11:00\ PM,\ how\ many\ reports\ did\ he\ staple\ altogether\?', 'MULT', ['val']),
    # freq=2
    (r'At\ a\ spa,\ Iris\ spent\ \$400\ to\ do\ her\ hair,\ 1/4\ as\ much\ to\ do\ a\ manicure,\ and\ 3/4\ as\ much\ money\ as\ a\ manicure\ to\ do\ a\ pedicure\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ than\ <OBJ>\ <OBJ>\ \|\ than\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ by\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ Jessica\ wants\ to\ pay\ 50%\ more\ than\ the\ minimum,\ how\ much\ does\ she\ pay\ in\ a\ year\?', 'MULT', ['val']),
    # freq=2
    (r'The\ bagel\ cost\ \$4,\ and\ the\ soup\ 25%\ more\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ quarter\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ quarter\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'At\ check\ out,\ Marcus\ shows\ his\ loyalty\ card\ that\ gives\ him\ 10%\ off\ of\ his\ purchase\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ buys\ <N>\ <OBJ>\ of\ a\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'The\ stock\ price\ increases\ 50%\ the\ first\ year\ Maria\ holds\ it,\ then\ decreases\ 25%\ in\ the\ second\ year\.', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ are\ <OBJ>\ each\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ this\ continues,\ how\ many\ chairs\ in\ total\ will\ Candy\ be\ able\ to\ rent\ out\ in\ two\ 4\-week\ months\?', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ buys\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ a', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <ENT>\ <OBJ>\ to\ make\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ make\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'albert's\ <OBJ>\ is\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ true/false\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=2
    (r'The\ red\ ties\ cost\ 50%\ more\ than\ blue\ ties\.', 'MULT', ['val']),
    # freq=2
    (r'if\ he\ bought\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ much', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <ENT>\ <ENT>\ <OBJ>\ <N>\ <ENT>\ \|\ <OBJ>\ <N>\ <ENT>\ <ENT>\ <OBJ>\ <N>\ <ENT>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'to\ <ENT>\ <ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ on\ a\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ sold\ <N>\ <OBJ>\ <OBJ>\ \$1\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ \$1\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$4\ each', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ every\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ is\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ is\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ is\ <OBJ>\ a\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ a\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ sells\ <N>\ <OBJ>\ <OBJ>\ \$2\ <OBJ>\ each\ \|\ \$2\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ at\ \$1\ each', 'MULT', ['val']),
    # freq=2
    (r'a\ company's\ hr\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ every\ <OBJ>\ to', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ ate\ <N>\ more\ <OBJ>\ than\ each\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ <OBJ>\ <OBJ>\ <N>\ times\ a\ <OBJ>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=2
    (r'She\ wants\ to\ save\ up\ 20%\ of\ the\ cost\ of\ a\ \$10000\ car\ for\ a\ downpayment\.', 'MULT', ['val']),
    # freq=2
    (r'if\ suzy’s\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'a\ uv\ <OBJ>\ <OBJ>\ on\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'many\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ in\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ he\ <OBJ>\ every\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'The\ cost\ for\ the\ pool\ company\ to\ come\ and\ fill\ the\ pool\ is\ \$0\.10\ per\ gallon\.', 'MULT', ['val']),
    # freq=2
    (r'if\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ many\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ he\ gets\ paid\ \$50\ every\ day,\ how\ much\ does\ he\ earn\ if\ he\ works\ for\ a\ year\?', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ at\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'if\ it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'It\ cost\ \$\.1\ per\ cubic\ foot\ to\ fill\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ by\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ in\ a\ <OBJ>\ is\ <N>', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ is\ <ENT>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ an\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ do', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ on\ <ENT>\ <OBJ>\ bought\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ bought\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ bought\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$4\ each', 'MULT', ['val']),
    # freq=2
    (r'At\ the\ local\ Pick\ Your\ Own\ fruit\ orchard,\ you\ could\ pick\ your\ own\ peaches\ for\ \$2\.00\ per\ pound,\ plums\ were\ \$1\.00\ per\ pound\ and\ apricots\ were\ \$3\.00\ per\ pound\.', 'MULT', ['val']),
    # freq=2
    (r'on\ <ENT>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ <OBJ>\ it\ at\ <OBJ>\ <N>\ times\ a\ <OBJ>\ <OBJ>\ makes\ \|\ times\ a\ <OBJ>\ <OBJ>\ makes\ <N>\ <OBJ>\ each\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'to\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ times\ a\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ times\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ he\ \|\ <OBJ>\ he\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ at\ a\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ at\ a\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ to\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ buys\ <N>\ <OBJ>\ of\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ had\ <N>\ times\ more\ <OBJ>\ than\ <OBJ>\ \|\ times\ more\ <OBJ>\ than\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'A\ bail\ of\ hay\ costs\ \$3\.', 'MULT', ['val']),
    # freq=2
    (r'he\ bought\ <N>\ <OBJ>\ <OBJ>\ cost\ \$1\.5\ each\ \|\ <OBJ>\ <OBJ>\ cost\ \$1\.5\ each\ <N>\ <OBJ>\ <OBJ>\ cost\ \$4\ each', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ every\ <OBJ>\ <OBJ>\ \|\ every\ <OBJ>\ <OBJ>\ <OBJ>\ on\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ \|\ each\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ every\ <OBJ>\ left', 'MULT', ['val']),
    # freq=2
    (r'he\ <OBJ>\ to\ work\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Hannah's\ house\ is\ at\ the\ right\ angle\ to\ see\ 40%\ of\ the\ city's\ fireworks\.', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ eats\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ it\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ it\ to\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ of\ \|\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ sells\ <N>\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ has\ a\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'to\ <OBJ>\ <OBJ>\ <OBJ>\ buys\ <N>\ <OBJ>\ <OBJ>\ \$500\ each\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ \$500\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \$1500\ each', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Scarlett\ found\ an\ aquarium\ for\ \$10\.00\ at\ a\ yard\ sale\.', 'MULT', ['val']),
    # freq=2
    (r'if\ he\ eats\ <N>\ <OBJ>\ each\ on\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ each\ on\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ on\ <ENT>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'He\ usually\ sells\ marigolds\ for\ \$2\.74\ per\ pot,\ petunias\ for\ \$1\.87\ per\ pot\ and\ begonias\ for\ \$2\.12\ per\ pot\.', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'a\ 5\-year\-old\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ 6\-year\-old\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ a\ 6\-year\-old\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>\ of\ \|\ <OBJ>\ a\ 7\-year\-old\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ an\ 8\-year\-old\ <OBJ>\ <N>\ <OBJ>\ less\ than\ a\ 10\-year\-old', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <ENT>\ he\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$20\ each\ \|\ <OBJ>\ <OBJ>\ \$20\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ \$10\ each', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ were\ <OBJ>\ <OBJ>\ of', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ 30%\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'One\ has\ 1/6\ left,\ the\ second\ has\ 2/3\ left\ and\ the\ third\ one\ has\ 1/2\ left\.', 'MULT', ['val']),
    # freq=2
    (r'Tabitha\ agreed\ to\ pay\ John\ and\ Jill\ \$10\ an\ hour\ to\ help\ clean\ out\ her\ attic\ and\ basement\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>', 'MULT', ['val']),
    # freq=2
    (r'a\ quarter\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'He\ gets\ a\ 10%\ commission\ on\ each\ copy\ of\ the\ New\ York\ Times\ and\ an\ 8%\ commission\ on\ each\ of\ the\ Wall\ Street\ Journal\.', 'MULT', ['val']),
    # freq=2
    (r'She\ smashes\ a\ quarter\ of\ the\ students'\ cars'\ windows\ and\ 3/4ths\ of\ the\ teachers'\ cars'\ windows\.', 'MULT', ['val']),
    # freq=2
    (r'Ronnie\ was\ given\ \$5\ while\ Rissa\ was\ given\ thrice\ as\ much\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Watson\ works\ a\ 10\-hour\ shift\ each\ day,\ five\ days\ a\ week\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ he\ \|\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'The\ cost\ of\ an\ adult\ ticket\ is\ \$12\ and\ a\ child\ ticket\ is\ \$8\.', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ were\ <OBJ>\ <OBJ>\ have\ \|\ have\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ to\ buy\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'in\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ he\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ he\ <OBJ>\ <N>\ <OBJ>\ every\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'in\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ kg\ of\ <OBJ>\ every\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ in\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'If\ she\ spent\ all\ the\ quarters\ and\ 3/5\ of\ the\ twenties,\ calculate\ the\ total\ amount\ of\ money\ she\ paid\ for\ the\ lunch\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ is\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ is\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'was\ <OBJ>\ roll\-ups\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ up\ <OBJ>\ <OBJ>\ marcell's\ \|\ up\ <OBJ>\ <OBJ>\ marcell's\ was\ <N>\ roll\-ups\ <OBJ>\ <OBJ>\ <N>\ roll\-ups\ \|\ was\ <N>\ roll\-ups\ <OBJ>\ <OBJ>\ <N>\ roll\-ups\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ has\ <N>\ 2\-legged\ <OBJ>\ <OBJ>\ <N>\ 4\-legged\ \|\ has\ <N>\ 2\-legged\ <OBJ>\ <OBJ>\ <N>\ 4\-legged\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Jamaar\ loves\ fresh\ fruit\ and\ is\ headed\ to\ the\ store\ with\ \$10\ he\ earned\ mowing\ lawns\.', 'MULT', ['val']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'much\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ of\ <N>\ third\-graders\ <OBJ>\ \|\ <N>\ <OBJ>\ of\ <N>\ third\-graders\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ third\-graders\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ half\ a\ <OBJ>\ in\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ it\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ are\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ is\ <OBJ>\ a\ <N>\ gb\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ makes\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ \|\ he\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ \|\ has\ <N>\ <OBJ>\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ \|\ <N>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'The\ suits\ cost\ \$750\ each\ and\ the\ dress\ pants\ cost\ 1/5\ that\ cost\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'it\ <OBJ>\ <ENT>\ <N>\ <OBJ>\ to\ <OBJ>\ a\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ a\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ a\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ 40%\ of', 'MULT', ['val']),
    # freq=2
    (r'each\ had\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ <OBJ>\ many\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'if\ it\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ at\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ a\ total\ of\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ a', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ to\ make\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ to\ make\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'it\ <OBJ>\ <ENT>\ <N>\ <OBJ>\ to\ <OBJ>\ to\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ half\ \|\ <OBJ>\ half\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'is\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ by\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ by\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'andy's\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ per\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ <OBJ>\ to\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ more\ <ENT>\ <ENT>\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <N>\ sq\ ft\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Colby\ loves\ going\ to\ the\ movies\ and\ every\ month\ his\ parents\ give\ him\ \$150\ to\ spend\ at\ the\ movies\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Ali\ has\ four\ \$10\ bills\ and\ six\ \$20\ bills\ that\ he\ saved\ after\ working\ for\ Mr\.', 'MULT', ['val']),
    # freq=2
    (r'Ali\ gives\ her\ sister\ half\ of\ the\ total\ money\ he\ has\ and\ uses\ 3/5\ of\ the\ remaining\ amount\ of\ money\ to\ buy\ dinner\.', 'MULT', ['val']),
    # freq=2
    (r'One\ pound\ of\ beeswax\ and\ the\ wicks\ cost\ \$10\.00\ in\ supplies\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ had\ <N>\ <OBJ>\ 2/5\ of\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'He\ can\ buy\ rocks\ for\ \$5\ each\ and\ sell\ them\ for\ \$7\ each\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ an\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<N>\ <OBJ>\ are\ <OBJ>\ to\ work', 'MULT', ['val']),
    # freq=2
    (r'One\ notebook\ is\ sold\ at\ \$1\.50\ each,\ a\ pen\ at\ \$0\.25\ each,\ a\ calculator\ at\ \$12\ each,\ and\ a\ geometry\ set\ at\ \$10\.', 'MULT', ['val']),
    # freq=2
    (r'to\ sell\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ has\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ of\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ are', 'MULT', ['val']),
    # freq=2
    (r'Rose\ bought\ five\ dozens\ of\ eggs\ for\ \$2\.40\ a\ dozen\.', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ if\ he\ has\ <N>\ <OBJ>\ at\ <OBJ>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'Zaid\ spends\ 1/4\ of\ his\ salary\ on\ rent,\ 1/3\ on\ car\ fuel\ and\ donates\ half\ of\ the\ remaining\ amount\ to\ his\ favorite\ charity\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <ENT>\ <OBJ>\ <ENT>\ bought\ <N>\ kg\ of\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ by\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ by\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ each', 'MULT', ['val']),
    # freq=2
    (r'Theo\ has\ \$6000\ he\ wishes\ to\ spend\ on\ his\ upcoming\ business\ trip\ to\ South\ Africa\.', 'MULT', ['val']),
    # freq=2
    (r'A\ pencil\ cost\ \$0\.50,\ and\ an\ eraser\ cost\ \$0\.25\.', 'MULT', ['val']),
    # freq=2
    (r'Howard\ spends\ \$8\ dollars\ at\ the\ arcade\ on\ Monday\.', 'MULT', ['val']),
    # freq=2
    (r'A\ basket\ of\ green\ food\ costs\ \$25\ and\ a\ basket\ of\ red\ food\ costs\ \$18\.', 'MULT', ['val']),
    # freq=2
    (r'In\ a\ student\ council\ election,\ candidate\ A\ got\ 20%\ of\ the\ votes\ while\ candidate\ B\ got\ 50%\ more\ than\ candidate\ A's\ votes\.', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ times', 'MULT', ['val']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ be\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ be\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=2
    (r'<ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'MULT', ['val']),
    # freq=5
    (r'My\ wife\ wants\ to\ evenly\ split\ the\ check\ but\ wants\ me\ to\ pay\ an\ additional\ 20%\ tip\ on\ our\ \$50\ dinner\ bill\.', 'PARTITION', ['groups']),
    # freq=5
    (r'a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ among\ <OBJ>\ <N>\ is\ \|\ <OBJ>\ <N>\ <OBJ>\ among\ <OBJ>\ <N>\ is\ <OBJ>\ 20%\ are\ <OBJ>\ \|\ is\ <OBJ>\ 20%\ are\ <OBJ>\ <N>\ are\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'PARTITION', ['groups']),
    # freq=4
    (r'In\ a\ 60\-item\ quiz,\ 40%\ of\ the\ questions\ are\ easy,\ and\ the\ rest\ are\ equally\ divided\ as\ average\ and\ difficult\ questions\.', 'PARTITION', ['groups']),
    # freq=3
    (r'<ENT>\ sold\ a\ total\ of\ <N>\ <OBJ>\ among\ <OBJ>\ <OBJ>\ <OBJ>', 'PARTITION', ['groups']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ was\ divided\ by\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ was\ \|\ by\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>', 'PARTITION', ['groups']),
    # freq=3
    (r'a\ <OBJ>\ of\ <N>\ <OBJ>\ is\ split\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ is\ split\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ of\ <OBJ>\ are\ <OBJ>\ in\ \|\ <OBJ>\ is\ <OBJ>\ <OBJ>\ is\ <N>\ less\ than\ each\ of\ <OBJ>', 'PARTITION', ['groups']),
    # freq=2
    (r'Gerald\ and\ Julia\ divided\ \$100\ in\ the\ ratio\ 3:2\.', 'PARTITION', ['groups']),
    # freq=2
    (r'of\ <OBJ>\ is\ divided\ <OBJ>\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ each\ \|\ divided\ <OBJ>\ <N>\ <OBJ>\ of\ <N>\ <OBJ>\ each', 'PARTITION', ['groups']),
    # freq=2
    (r'<OBJ>\ county\-level\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ were\ <OBJ>\ to\ split', 'PARTITION', ['groups']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'PARTITION', ['groups']),
    # freq=5
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=5
    (r'<ENT>\ <OBJ>\ at\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=4
    (r'in\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ \$15', 'RATE', ['ent', 'rate']),
    # freq=4
    (r'Valerie\ earns\ \$5000\ per\ month,\ 1/2\ of\ what\ her\ brother\ earns\.', 'RATE', ['ent', 'rate']),
    # freq=3
    (r'a\ <OBJ>\ eats\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ per\ <OBJ>\ <OBJ>\ <OBJ>\ eats\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ eats\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=3
    (r'a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=3
    (r'He\ earns\ \$10\ per\ hour\ and\ gets\ a\ \$300\ bonus\ each\ week\ if\ the\ company\ performs\ well\.', 'RATE', ['ent', 'rate']),
    # freq=3
    (r'<OBJ>\ at\ a\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ an\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ an\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>\ less\ than', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'per\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ work', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'His\ standard\ fee\ is\ \$80\ per\ hour\ for\ lessons,\ but\ he\ reduces\ his\ rate\ by\ 25%\ when\ he\ is\ giving\ lessons\ to\ a\ veteran\.', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'per\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ works\ each\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'if\ he\ <OBJ>\ <N>\ less\ than\ <N>\ <OBJ>\ per\ \|\ he\ <OBJ>\ <N>\ less\ than\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ much', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'earns\ \$20\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ work\ each\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <N>\ large\-sized\ <OBJ>\ <OBJ>\ per\ <OBJ>\ \|\ <OBJ>\ or\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ medium\-sized\ <OBJ>\ <OBJ>\ per\ <OBJ>\ \|\ <OBJ>\ or\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ small\-sized\ <OBJ>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'The\ normal\ price\ is\ \$1500\ per\ day\.', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'if\ a\ <ENT>\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ a\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ per', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'he\ eats\ <N>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'ada's\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'a\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>\ a\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'If\ a\ kilowatt\ per\ hour\ is\ \$1\.50,\ how\ much\ is\ the\ difference\ between\ Ada's\ weekly\ electric\ bill\ before\ and\ after\ she\ adds\ the\ new\ device\?', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'he\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ a\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'of\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ if\ <OBJ>\ works\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'much\ <OBJ>\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ if\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ per\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'in\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ at\ a\ <OBJ>\ of\ \|\ <OBJ>\ at\ a\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ at\ a\ <OBJ>\ of\ \|\ <OBJ>\ at\ a\ <OBJ>\ of\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ is\ <OBJ>\ <N>\ <OBJ>\ an\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ to\ be\ <N>\ <OBJ>\ per\ <OBJ>\ <OBJ>\ <OBJ>', 'RATE', ['ent', 'rate']),
    # freq=6
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <ENT>', 'THERE_ARE', ['count', 'container']),
    # freq=6
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ a\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=5
    (r'of\ <OBJ>\ <OBJ>\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ 60%\ more', 'THERE_ARE', ['count', 'container']),
    # freq=4
    (r'if\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=4
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ there\ <OBJ>\ <ENT>', 'THERE_ARE', ['count', 'container']),
    # freq=4
    (r'<ENT>\ are\ <N>\ <OBJ>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=4
    (r'if\ there\ were\ <N>\ <OBJ>\ <OBJ>\ many\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'<ENT>\ <OBJ>\ if\ there\ are\ <N>\ multiple\-choice\ <OBJ>\ <N>\ true/false\ <OBJ>\ \|\ there\ are\ <N>\ multiple\-choice\ <OBJ>\ <N>\ true/false\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ true/false\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ of\ <OBJ>\ is\ <N>\ <OBJ>\ many\ <OBJ>\ in\ total', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'if\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ \|\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ a\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'if\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ \|\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ every\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'if\ there\ are\ <N>\ <ENT>\ <OBJ>\ <OBJ>\ many\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'There\ are\ 9,300\ pennies\ in\ a\ cup\.', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'<ENT>\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=3
    (r'tate’s\ <OBJ>\ <OBJ>\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ is\ <N>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'if\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ \|\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ were\ <N>\ <OBJ>\ in\ each\ <OBJ>\ of\ \|\ each\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ in\ each\ <OBJ>\ of', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <N>\ more\ <OBJ>\ <OBJ>\ an\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ bought\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ gave\ \|\ <OBJ>\ of\ <OBJ>\ <OBJ>\ gave\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ if\ \|\ <OBJ>\ <OBJ>\ if\ there\ are\ <N>\ <OBJ>\ of\ <OBJ>\ per\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ <OBJ>\ has\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ on\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ there\ are\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ there\ are\ <N>\ more\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ there\ are\ <N>\ <OBJ>\ in\ <ENT>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <N>\ in\ a\ <OBJ>\ <OBJ>\ there\ \|\ a\ <OBJ>\ <OBJ>\ there\ are\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ \|\ are\ <N>\ <OBJ>\ each\ <OBJ>\ <N>\ <OBJ>\ <ENT>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <N>\ <OBJ>\ of\ <OBJ>\ left\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'if\ there\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ in', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ are\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ in\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'in\ <OBJ>\ <OBJ>\ there\ are\ <N>\ <OBJ>\ of\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ are\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ <OBJ>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ there\ are', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ were\ <N>\ <OBJ>\ on\ a\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ there\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ more\ \|\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ has\ <OBJ>\ <OBJ>\ <N>\ times\ <OBJ>\ <OBJ>\ <OBJ>\ has\ \|\ <OBJ>\ <OBJ>\ has\ <OBJ>\ <OBJ>\ <N>\ times', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'there\ are\ a\ total\ of\ <N>\ <OBJ>\ <OBJ>\ in\ total\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'if\ there\ are\ <N>\ <OBJ>\ in\ <OBJ>\ <OBJ>\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=2
    (r'<ENT>\ are\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <OBJ>', 'THERE_ARE', ['count', 'container']),
    # freq=6
    (r'<OBJ>\ had\ <N>\ <OBJ>\ <OBJ>\ twice\ as\ many', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=5
    (r'<ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ \|\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ <OBJ>\ twice', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=5
    (r'Each\ uniform\ comes\ with\ a\ hat\ that\ costs\ \$25,\ a\ jacket\ that\ costs\ three\ times\ as\ much\ as\ the\ hat,\ and\ pants\ that\ cost\ the\ average\ of\ the\ costs\ of\ the\ hat\ and\ jacket\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=5
    (r'<OBJ>\ <OBJ>\ <N>\ <OBJ>\ 1/3rd\ as\ many\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <N>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'<OBJ>\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ more\ <OBJ>\ than\ on\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'<ENT>\ were\ <N>\ <OBJ>\ <N>\ fewer\ <OBJ>\ than\ \|\ <ENT>\ were\ <N>\ <OBJ>\ <N>\ fewer\ <OBJ>\ than\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'He\ buys\ a\ mobile\ device\ for\ \$20\ and\ sells\ it\ for\ twice\ the\ amount\ of\ the\ original\ price\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'The\ pasta\ costs\ \$1\.00\ a\ box,\ and\ he\ spends\ \$3\.00\ on\ cheddar\ cheese\ and\ twice\ that\ amount\ for\ the\ gruyere\ cheese\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'<ENT>\ has\ <N>\ times\ as\ many\ <OBJ>\ as', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'One\ apple\ costs\ \$0\.5\ and\ one\ banana\ costs\ twice\ as\ much\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=4
    (r'<ENT>\ <N>\ <OBJ>\ <OBJ>\ had\ a\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<ENT>\ third\ <OBJ>\ is\ <N>\ mm\ less\ <OBJ>\ than\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'in\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ be\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ be\ <N>\ <OBJ>\ <OBJ>\ than\ twice\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'If\ he\ had\ a\ 25k\ a\ year\ job\ before\ college\ and\ his\ college\ degree\ tripled\ his\ income,\ how\ long\ would\ it\ take\ to\ earn\ the\ money\ equivalent\ to\ the\ loans\ and\ the\ money\ lost\ from\ not\ working\ while\ in\ school\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'He\ also\ buys\ twice\ as\ many\ bottles\ of\ cognac\ that\ cost\ 50%\ more\ per\ bottle\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'If\ his\ father\ also\ gave\ him\ 2/5\ times\ as\ many\ marbles\ as\ he\ bought\ from\ Johanna,\ and\ each\ marble\ weighs\ 2kgs,\ calculate\ the\ total\ weight\ of\ marbles\ Solomon\ has\ in\ the\ store\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<OBJ>\ as\ he\ has\ <OBJ>\ <N>\ more\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'On\ the\ second\ race,\ he\ won\ \$1\ more\ than\ twice\ the\ amount\ he\ previously\ lost\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ of', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<OBJ>\ <ENT>\ <ENT>\ <ENT>\ makes\ <N>\ <OBJ>\ on\ <ENT>\ <N>\ <OBJ>\ \|\ makes\ <N>\ <OBJ>\ on\ <ENT>\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ twice', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'a\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ has\ twice\ as\ many', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'<OBJ>\ <N>\ <OBJ>\ of\ <OBJ>\ cost\ \$10\ \|\ in\ total\ <OBJ>\ <OBJ>\ has\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ each', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=3
    (r'The\ number\ of\ downloads\ in\ the\ second\ month\ was\ three\ times\ as\ many\ as\ the\ downloads\ in\ the\ first\ month,\ but\ then\ reduced\ by\ 30%\ in\ the\ third\ month\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'The\ first\ paid\ hour\ is\ \$15\ and\ each\ hour\ after\ that\ is\ twice\ the\ cost\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'he\ sold\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ x\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'on\ <ENT>\ <ENT>\ ate\ <N>\ times\ as\ many\ <OBJ>\ as', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'at\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'He\ sells\ 20%\ of\ them\ and\ gives\ away\ twice\ as\ many\ cars\ as\ the\ number\ he\ sold\ to\ his\ mother\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'On\ eBay,\ those\ same\ pair\ of\ shoes\ are\ only\ \$13,\ but\ shipping\ costs\ twice\ as\ much\ as\ it\ does\ on\ Amazon\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<ENT>\ <OBJ>\ <OBJ>\ <N>\ more\ <OBJ>\ were\ <OBJ>\ at', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'He\ buys\ a\ package\ of\ fireworks\ worth\ \$400\ and\ another\ pack\ worth\ twice\ that\ much\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<OBJ>\ third\ <OBJ>\ he\ <OBJ>\ <N>\ times\ as\ much\ as\ he', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'as\ <ENT>\ <OBJ>\ <ENT>\ makes\ <N>\ more\ <OBJ>\ <OBJ>\ than\ <ENT>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<ENT>\ <OBJ>\ to\ <OBJ>\ <N>\ more\ than\ double\ <OBJ>\ <OBJ>\ \|\ in\ a\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'if\ there\ are\ <N>\ <OBJ>\ in\ a\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'he\ <OBJ>\ to\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ twice\ as', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<ENT>\ has\ <N>\ <OBJ>\ <OBJ>\ <ENT>\ had\ twice\ \|\ sarah’s\ <OBJ>\ <OBJ>\ he\ <OBJ>\ <N>\ of\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'on\ <ENT>\ <OBJ>\ <OBJ>\ <N>\ more\ than\ twice\ as\ many', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'it\ <OBJ>\ <N>\ <OBJ>\ on\ <ENT>\ <OBJ>\ is\ \|\ <OBJ>\ is\ <OBJ>\ to\ <OBJ>\ <N>\ more\ <OBJ>\ than\ twice\ of', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'After\ a\ while,\ twice\ the\ number\ of\ people\ who\ entered\ the\ restaurant\ at\ 10:00\ came\ in\ and\ ordered\ lunch\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'if\ <ENT>\ is\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ \|\ <OBJ>\ <OBJ>\ <OBJ>\ be\ in\ <N>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'alain's\ <OBJ>\ bought\ <N>\ <OBJ>\ of\ <OBJ>\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<ENT>\ are\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ twice', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'he\ has\ <N>\ times\ as\ many\ <OBJ>\ as', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'His\ mother\ gave\ him\ \$6\ for\ this\ purpose,\ and\ his\ father\ gave\ him\ twice\ as\ much\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'Marissa\ makes\ 3/4\ times\ as\ many\ pounds\ of\ chocolates\ in\ an\ hour\ as\ Ruiz\ makes\ in\ the\ two\ hours\.', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<OBJ>\ of\ <OBJ>\ <OBJ>\ is\ <N>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'as\ <ENT>\ <OBJ>\ <ENT>\ <OBJ>\ <N>\ times\ as\ much\ <OBJ>\ as\ \|\ <ENT>\ do\ if\ <ENT>\ <OBJ>\ <N>\ <OBJ>\ of\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'on\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ \|\ <N>\ <OBJ>\ <OBJ>\ <OBJ>\ <OBJ>\ <N>\ times\ as\ many\ <OBJ>\ as', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'he\ buys\ <N>\ <OBJ>\ <OBJ>\ at\ \$100\ each\ \|\ <OBJ>\ <OBJ>\ at\ \$100\ each\ <N>\ <OBJ>\ at\ \$50\ each\ a\ \|\ <OBJ>\ costs\ \$700\ more\ than\ <N>\ times\ as\ much\ as\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
    # freq=2
    (r'<ENT>\ <OBJ>\ has\ <N>\ times\ as\ many\ <OBJ>\ <OBJ>', 'TIMES_AS_MANY', ['ent', 'mult']),
]